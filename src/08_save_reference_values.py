"""
08_save_reference_values.py
===========================
Calculates the median values used to fill missing data ONCE, from the full
dataset, and saves them to config/reference_values.json.

The weekly pipeline reads this file instead of calculating its own medians,
so every week fills missing values with the SAME numbers.

Run from the project root:
    python src/08_save_reference_values.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.db_config import PROJECT_ROOT, RAW_DIR

df = pd.read_csv(RAW_DIR / "customers_raw.csv")

# Same steps as 02_clean.py, in the same order, so the medians match
# 1. Invalid ages -> NaN
df.loc[(df["age"] < 18) | (df["age"] > 100), "age"] = np.nan

# 2. Dedup: keep the row with the fewest missing values
df["_null_count"] = df.isna().sum(axis=1)
df = (df.sort_values("_null_count")
        .drop_duplicates(subset=["customer_id"], keep="first")
        .drop(columns="_null_count"))
print("Rows after dedup:", len(df))

# 3. Medians
reference = {
    col: float(df[col].median())
    for col in ["age", "credit_score", "estimated_salary", "monthly_logins"]
}

out_path = PROJECT_ROOT / "config" / "reference_values.json"
with open(out_path, "w") as f:
    json.dump(reference, f, indent=2)

print("Saved:", out_path)
print(json.dumps(reference, indent=2))