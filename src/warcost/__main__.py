"""Command line entry point.

    python -m warcost fetch     download sources into data/processed
    python -m warcost analyse   run the model, write summaries and reports/key_numbers.json
    python -m warcost figures   draw figures/ (PNG and SVG)
    python -m warcost story     build docs/index.html, the narrative page
    python -m warcost all       all of the above
"""
from __future__ import annotations

import argparse
import logging

from .config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(prog="warcost")
    parser.add_argument("command", choices=["fetch", "analyse", "figures", "story", "all"])
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cfg = load_config()

    if args.command in ("fetch", "all"):
        from .sources import build_all
        build_all(cfg)
    if args.command in ("analyse", "all"):
        from .analysis import write_outputs
        write_outputs(cfg)
    if args.command in ("figures", "all"):
        from .figures import draw_all
        draw_all(cfg)
    if args.command in ("story", "all"):
        from .story import build_story
        build_story(cfg)


if __name__ == "__main__":
    main()
