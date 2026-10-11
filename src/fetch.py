"""Download and tidy the raw data.

    python -m src.fetch              # fetch everything
    python -m src.fetch --templates  # write manual-override CSV templates

Outputs (data/processed/):
    prices.csv       month x spending group, HICP index (any base)
    households.csv   one row per income quintile: spending shares, € spending, € income
"""
from __future__ import annotations

import argparse
import itertools
import re
from pathlib import Path

import pandas as pd
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
QUINTILES = ["Q1", "Q2", "Q3", "Q4", "Q5"]
SHARE_GROUPS = ["food", "home_energy", "motor_fuel"]

EUROSTAT_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{ds}"


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text())


# --------------------------------------------------------------------------- prices
def parse_jsonstat(js: dict) -> pd.DataFrame:
    """Turn a Eurostat JSON-stat 2.0 response into a long DataFrame."""
    ids, sizes = js["id"], js["size"]
    labels = []
    for dim in ids:
        idx = js["dimension"][dim]["category"]["index"]
        labels.append(sorted(idx, key=idx.get))
    rows = []
    for flat, combo in enumerate(itertools.product(*labels)):
        val = js["value"].get(str(flat))
        if val is not None:
            rows.append((*combo, val))
    assert len(rows) <= 1 or all(sizes), "empty dimension"
    return pd.DataFrame(rows, columns=[*ids, "value"])


def fetch_prices(cfg: dict) -> pd.DataFrame:
    p = cfg["prices"]
    frames = {}
    for group, code in p["groups"].items():
        params = {"geo": p["geo"], "coicop": code, "sinceTimePeriod": p["start"]}
        r = requests.get(EUROSTAT_URL.format(ds=p["dataset"]), params=params, timeout=60)
        r.raise_for_status()
        df = parse_jsonstat(r.json())
        # Prefer the oldest base still published; any base works because the model uses ratios.
        units = [u for u in ("I15", "I25", "I05") if u in set(df["unit"])] or sorted(set(df["unit"]))
        df = df[df["unit"] == units[0]]
        s = df.set_index("time")["value"].astype(float)
        s.index = pd.PeriodIndex(s.index.str.replace("M", "-"), freq="M")
        frames[group] = s.sort_index()
        print(f"  prices {group:12s} {code:15s} unit={units[0]} {s.index.min()}..{s.index.max()}")
    out = pd.DataFrame(frames).dropna(how="all")
    out.index.name = "month"
    return out


# ----------------------------------------------------------------------- CBS tables
def _cbs(table: str) -> pd.DataFrame:
    import cbsodata  # imported lazily so tests don't need network libs

    return pd.DataFrame(cbsodata.get_data(table))


def _find_col(df: pd.DataFrame, pattern: str) -> str:
    for col in df.columns:
        if df[col].dtype == object and df[col].astype(str).str.contains(pattern, case=False, regex=False).any():
            return col
    raise KeyError(f"no column contains a label matching {pattern!r}")


def _value_col(df: pd.DataFrame) -> str:
    num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != "ID"]
    if not num:
        raise KeyError("no numeric column")
    return num[0]


def _quintile_rows(df: pd.DataFrame, cfg: dict) -> tuple[str, dict]:
    pats = cfg["cbs"]["quintile_patterns"]
    qcol = _find_col(df, pats[0])
    mapping = {}
    for q, pat in zip(QUINTILES, pats):
        hits = df[qcol][df[qcol].astype(str).str.contains(pat, regex=False)].unique()
        # prefer the label that mentions income (besteedbaar/inkomen)
        hits = sorted(hits, key=lambda s: ("inkomen" not in s.lower(), len(s)))
        if not hits:
            raise KeyError(f"quintile {q} not found with {pat!r}")
        mapping[hits[0]] = q
    return qcol, mapping


def _filter_year(df: pd.DataFrame, year: str) -> pd.DataFrame:
    if "Perioden" in df.columns:
        df = df[df["Perioden"].astype(str).str.contains(year)]
    return df


def fetch_households(cfg: dict) -> pd.DataFrame:
    c = cfg["cbs"]
    year = c["survey_year"]

    # spending shares (% of total spending) per quintile
    sh = _filter_year(_cbs(c["spending_shares_table"]), year)
    qcol, qmap = _quintile_rows(sh, cfg)
    sh = sh[sh[qcol].isin(qmap)]
    vcol = _value_col(sh)
    catcol = _find_col(sh, c["category_patterns"]["food"])
    out = pd.DataFrame(index=QUINTILES)
    for g in SHARE_GROUPS:
        pat = c["category_patterns"][g]
        rows = sh[sh[catcol].str.contains(pat, case=False, regex=False)]
        # take the broadest matching category (shortest label) per quintile
        rows = rows.assign(_len=rows[catcol].str.len()).sort_values("_len").drop_duplicates(qcol)
        out[f"share_{g}"] = rows.set_index(rows[qcol].map(qmap))[vcol] / 100.0
        print(f"  share {g:12s} <- {rows[catcol].iloc[0]!r}")

    # € spending per household per year
    eu = _filter_year(_cbs(c["spending_euros_table"]), year)
    qcol, qmap = _quintile_rows(eu, cfg)
    eu = eu[eu[qcol].isin(qmap)]
    try:
        catcol = _find_col(eu, "totaal")
        eu = eu[eu[catcol].str.contains("totaal", case=False)]
        eu = eu.assign(_len=eu[catcol].str.len()).sort_values("_len").drop_duplicates(qcol)
    except KeyError:
        pass
    out["spending_eur_year"] = eu.set_index(eu[qcol].map(qmap))[_value_col(eu)]

    # € disposable income per household (optional)
    out["income_eur_year"] = float("nan")
    if c.get("income_table"):
        try:
            inc = _filter_year(_cbs(c["income_table"]), year)
            qcol, qmap = _quintile_rows(inc, cfg)
            inc = inc[inc[qcol].isin(qmap)]
            col = next(cc for cc in inc.columns if "besteedbaar" in cc.lower() and "gemiddeld" in cc.lower())
            vals = inc.drop_duplicates(qcol).set_index(inc.drop_duplicates(qcol)[qcol].map(qmap))[col]
            out["income_eur_year"] = vals * (1000 if vals.median() < 1000 else 1)  # CBS often reports ×1000
        except Exception as exc:  # noqa: BLE001
            print(f"  income table skipped ({exc}); dashboard falls back to % of spending")
    out.index.name = "quintile"
    return out


# ------------------------------------------------------------------ manual override
def write_templates(cfg: dict) -> None:
    (ROOT / cfg["manual"]["household_csv"]).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {"quintile": QUINTILES, **{f"share_{g}": [None] * 5 for g in SHARE_GROUPS},
         "spending_eur_year": [None] * 5, "income_eur_year": [None] * 5}
    ).to_csv(ROOT / cfg["manual"]["household_csv"], index=False)
    print(f"template written: {cfg['manual']['household_csv']} (shares as fractions, e.g. 0.12)")


def load_manual(cfg: dict) -> pd.DataFrame | None:
    path = ROOT / cfg["manual"]["household_csv"]
    if path.exists():
        df = pd.read_csv(path, index_col="quintile")
        required = [f"share_{g}" for g in SHARE_GROUPS] + ["spending_eur_year"]
        if df[required].notna().all(axis=None):
            print(f"  using manual household data from {path.name}")
            return df
    return None


def inspect(cfg: dict) -> None:
    """Dump the structure of every source table to data/debug/ (for fixing label patterns)."""
    import traceback

    debug = ROOT / "data" / "debug"
    debug.mkdir(parents=True, exist_ok=True)
    c = cfg["cbs"]
    for key in ("spending_shares_table", "spending_euros_table", "income_table"):
        table = c.get(key)
        if not table:
            continue
        try:
            df = _cbs(table)
            lines = [f"{table}: {len(df)} rows", f"columns: {list(df.columns)}", ""]
            for col in df.columns:
                if df[col].dtype == object:
                    vals = df[col].dropna().unique()
                    lines.append(f"[{col}] {len(vals)} unique")
                    lines += [f"   {v}" for v in vals[:80]]
            (debug / f"{table}_structure.txt").write_text("\n".join(lines))
            df.head(300).to_csv(debug / f"{table}_head.csv", index=False)
            print(f"  inspected {table}: {len(df)} rows")
        except Exception:  # noqa: BLE001
            (debug / f"{table}_error.txt").write_text(traceback.format_exc())
            print(f"  FAILED {table}")
    # Eurostat: which COICOP codes / units answer for NL
    p = cfg["prices"]
    lines = []
    for code in list(p["groups"].values()) + ["CP0451", "CP0452", "CP045_0451", "CP07221"]:
        r = requests.get(EUROSTAT_URL.format(ds=p["dataset"]),
                         params={"geo": p["geo"], "coicop": code, "sinceTimePeriod": "2025-01"}, timeout=60)
        if r.ok:
            df = parse_jsonstat(r.json())
            lines.append(f"{code}: OK units={sorted(set(df['unit']))} last={df['time'].max()}")
        else:
            lines.append(f"{code}: HTTP {r.status_code} {r.text[:200]}")
    (debug / "eurostat_codes.txt").write_text("\n".join(lines))
    print("\n".join(lines))


def main() -> None:
    import traceback

    ap = argparse.ArgumentParser()
    ap.add_argument("--templates", action="store_true")
    ap.add_argument("--inspect", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    if args.templates:
        write_templates(cfg)
        return
    if args.inspect:
        inspect(cfg)
        return
    PROCESSED.mkdir(parents=True, exist_ok=True)
    ok = True
    print("Fetching Eurostat HICP …")
    try:
        fetch_prices(cfg).to_csv(PROCESSED / "prices.csv")
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        ok = False
    print("Fetching CBS household tables …")
    try:
        hh = load_manual(cfg)
        if hh is None:
            hh = fetch_households(cfg)
        hh.to_csv(PROCESSED / "households.csv")
        print(hh.round(3))
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        ok = False
    print("Done → data/processed/" if ok else "FINISHED WITH ERRORS")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
