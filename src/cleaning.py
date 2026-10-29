"""
cleaning.py
===========
The customer cleaning rules from 02_clean.py, packaged as ONE reusable
function so the weekly pipeline (09_run_pipeline.py) applies exactly the
same rules to every file.

Two differences from 02_clean.py:
  1. Missing values are filled with FIXED reference medians loaded from
     config/reference_values.json (made by 08_save_reference_values.py),
     not with medians calculated from whatever rows are in the file.
  2. No printing or saving. The function takes a DataFrame and returns a
     cleaned DataFrame. The pipeline decides what to do with it.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_FILE = PROJECT_ROOT / "config" / "reference_values.json"

SNAPSHOT_DATE = pd.Timestamp("2026-09-01")

# Columns of the MySQL customers table, in order
CUSTOMER_COLUMNS = [
    "customer_id", "surname", "geography", "gender", "age", "credit_score",
    "tenure", "join_date", "balance", "estimated_salary", "num_products",
    "has_cr_card", "is_active_member", "branch_id", "segment",
    "complaints_last_year", "monthly_logins", "exited", "churn_date",
    "age_was_missing", "credit_score_was_missing", "estimated_salary_was_missing",
]


def load_reference_values():
    """Read the fixed medians saved by 08_save_reference_values.py."""
    with open(REFERENCE_FILE) as f:
        return json.load(f)


def clean_customers(df, ref):
    """Apply every cleaning rule from 02_clean.py to a batch of raw customers.

    df  : raw customer rows (one weekly file, or the full raw file)
    ref : dict of fixed medians, from load_reference_values()
    """
    df = df.copy()

    # 1. Invalid ages -> NaN (BEFORE dedup, so customer 117688's age-250 row
    #    gets an extra missing value and loses the dedup)
    df.loc[(df["age"] < 18) | (df["age"] > 100), "age"] = np.nan

    # 2. Standardize text categories
    df["geography"] = df["geography"].str.strip().str.title()
    df["gender"] = (df["gender"].str.strip().str.title()
                    .replace({"M": "Male", "F": "Female"}))

    # 3. Balance: remove the € symbol and convert to a number.
    #    astype("string") makes this work even if a file has no € at all
    #    and pandas already read the column as numbers.
    df["balance"] = pd.to_numeric(
        df["balance"].astype("string").str.replace("€", "", regex=False).str.strip(),
        errors="coerce")

    # 4. Dedup inside this batch: keep the row with the fewest missing values
    df["_null_count"] = df.isna().sum(axis=1)
    df = (df.sort_values("_null_count", kind="stable")
            .drop_duplicates(subset=["customer_id"], keep="first")
            .drop(columns="_null_count"))

    # 5. Future-dated churn (issue #7): still a customer on the snapshot date
    df["churn_date"] = pd.to_datetime(df["churn_date"], errors="coerce")
    future = df["churn_date"] > SNAPSHOT_DATE
    df.loc[future, "exited"] = 0
    df.loc[future, "churn_date"] = pd.NaT

    # 6. Fill missing values with the FIXED reference medians + flag them
    for col in ["age", "credit_score", "estimated_salary"]:
        df[f"{col}_was_missing"] = df[col].isna().astype(int)
        df[col] = df[col].fillna(ref[col])

    # monthly_logins: median fill, no flag (same as 02_clean.py)
    df["monthly_logins"] = df["monthly_logins"].fillna(ref["monthly_logins"])

    return df[CUSTOMER_COLUMNS].reset_index(drop=True)