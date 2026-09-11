"""
01_load_raw.py
==============
STEP 1: Look at the data. Do NOT clean anything yet.

The point of this script is to answer: what am I actually dealing with?
Every cleaning decision you make later should come from what you see here.

Run it:
    python src/01_load_raw.py
"""

import sys
from pathlib import Path

import pandas as pd

# Let this script import from config/
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.db_config import RAW_DIR


# ----------------------------------------------------------------------
# Which files we expect to find
# ----------------------------------------------------------------------
FILES = {
    "customers":         "customers_raw.csv",
    "branches":          "branches.csv",
    "products":          "products.csv",
    "customer_products": "customer_products.csv",
    "loans":             "loans.csv",
    "monthly_activity":  "monthly_activity.csv",
}


def line(char="-", width=70):
    print(char * width)


def profile(name, df):
    """Print a summary of one table."""
    line("=")
    print(f"TABLE: {name}")
    line("=")

    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Memory:  {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

    # --- duplicates ---
    dupes = df.duplicated().sum()
    flag = "  <-- NEEDS FIXING" if dupes > 0 else ""
    print(f"\nFull duplicate rows: {dupes:,}{flag}")

    # --- column by column ---
    print("\nColumns:")
    print(f"  {'name':<24} {'dtype':<12} {'nulls':>8} {'null %':>8} {'unique':>9}")
    line()
    for col in df.columns:
        nulls = df[col].isna().sum()
        pct = nulls / len(df) * 100
        nuniq = df[col].nunique(dropna=True)
        mark = "  <--" if pct > 0 else ""
        print(f"  {col:<24} {str(df[col].dtype):<12} "
              f"{nulls:>8,} {pct:>7.2f}% {nuniq:>9,}{mark}")

    # --- categorical columns: show every value ---
    # Anything with few unique values is worth eyeballing in full,
    # because that is where inconsistent labels hide.
    print("\nLow-cardinality columns (check these for inconsistent labels):")
    found_any = False
    for col in df.columns:
        nuniq = df[col].nunique(dropna=True)
        is_text = df[col].dtype == object or str(df[col].dtype) in ("str", "string")
        if 0 < nuniq <= 15 and is_text:
            found_any = True
            vals = sorted(df[col].dropna().unique().tolist(), key=str)
            print(f"  {col}  ({nuniq} values)")
            print(f"    {vals}")
    if not found_any:
        print("  (none)")

    # --- numeric summary ---
    num = df.select_dtypes(include="number")
    if not num.empty:
        print("\nNumeric summary (look for impossible min/max values):")
        summary = num.describe().T[["min", "mean", "max"]]
        print(summary.to_string(float_format=lambda x: f"{x:,.2f}"))

    # --- first few rows ---
    print("\nFirst 3 rows:")
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(df.head(3).to_string())

    print()


def main():
    print("\nReading files from:", RAW_DIR, "\n")

    missing = [f for f in FILES.values() if not (RAW_DIR / f).exists()]
    if missing:
        print("MISSING FILES — put these in data/raw/ first:")
        for f in missing:
            print("   -", f)
        return

    tables = {}
    for name, filename in FILES.items():
        df = pd.read_csv(RAW_DIR / filename)
        tables[name] = df
        profile(name, df)

    # ------------------------------------------------------------------
    # Cross-table checks: do the foreign keys actually match up?
    # ------------------------------------------------------------------
    line("=")
    print("RELATIONSHIP CHECKS")
    line("=")

    cust = tables["customers"]
    br = tables["branches"]
    cp = tables["customer_products"]
    ln = tables["loans"]

    orphan_branches = set(cust.branch_id) - set(br.branch_id)
    print(f"Customers pointing at a branch that doesn't exist: {len(orphan_branches)}")

    orphan_cp = set(cp.customer_id) - set(cust.customer_id)
    print(f"Product rows pointing at a customer that doesn't exist: {len(orphan_cp)}")

    orphan_loans = set(ln.customer_id) - set(cust.customer_id)
    print(f"Loans pointing at a customer that doesn't exist: {len(orphan_loans)}")

    print(f"\nUnique customer_id values: {cust.customer_id.nunique():,}")
    print(f"Total rows in customers:   {len(cust):,}")
    if cust.customer_id.nunique() < len(cust):
        gap = len(cust) - cust.customer_id.nunique()
        print(f"  --> {gap:,} rows share an ID with another row. Duplicates to remove.")

    line("=")
    print("DONE. Now write down what you found before you clean anything.")
    line("=")


if __name__ == "__main__":
    main()
