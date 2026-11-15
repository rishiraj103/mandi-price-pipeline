"""Clean and model raw dates on the laptop.

Usage:
    python -m transform.run_local --all
    python -m transform.run_local 2026-11-20 2026-11-19
"""
import argparse
from datetime import date
from pathlib import Path

from transform import build_model, clean_day


def main():
    p = argparse.ArgumentParser()
    p.add_argument("dates", nargs="*", type=date.fromisoformat)
    p.add_argument("--all", action="store_true", help="every raw date that has a manifest")
    p.add_argument("--base", default="data")
    args = p.parse_args()

    dates = args.dates
    if args.all:
        dates = sorted(date.fromisoformat(m.parent.name.split("=")[1])
                       for m in Path(args.base, "raw").glob("arrival_date=*/_manifest.json"))

    dim_date = Path(args.base, "model", "dim_date", "dim_date.parquet")
    if not dim_date.exists():
        dim_date.parent.mkdir(parents=True, exist_ok=True)
        build_model.build_dim_date().to_parquet(dim_date, index=False)

    for day in dates:
        curated, dq = clean_day.run(day, args.base)
        fact = build_model.run(curated, day, args.base)
        print(f"{day}  read={dq['rows_read']:5}  passed={dq['rows_passed']:5}  "
              f"rejected={dq['rows_rejected']:3}  outliers={dq['outliers_flagged']:3}  fact={len(fact)}")


if __name__ == "__main__":
    main()
