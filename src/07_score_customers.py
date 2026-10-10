"""
07_score_customers.py
=====================
Scores every customer with an out-of-fold churn probability and saves:
  - MySQL table `churn_scores`         -> feeds Power BI through vw_customers
  - outputs/high_risk_customers.csv    -> top 500 retained customers by expected loss

Why out-of-fold: scoring customers the model was trained on gives inflated,
overconfident probabilities (lots of 1.00 and 0.95). cross_val_predict scores
each customer with a model trained on the other 80% of customers.

Run from the project root:
    python src/07_score_customers.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.db_config import OUTPUT_DIR, PROCESSED_DIR, RAW_DIR, get_engine


# ============================================================
# 1. LOAD DATA
# ============================================================
df = pd.read_csv(PROCESSED_DIR / "customers_clean.csv")
activity = (pd.read_csv(RAW_DIR / "monthly_activity.csv")
            .sort_values(["customer_id", "activity_month"]))


# ============================================================
# 2. TREND FEATURES (same logic as 06_model.py)
# ============================================================
by_cust = activity.groupby("customer_id")
trend = pd.DataFrame({
    "early_txn": by_cust.head(3).groupby("customer_id")["num_transactions"].mean(),
    "recent_txn": by_cust.tail(3).groupby("customer_id")["num_transactions"].mean(),
})
trend["txn_change"] = trend["recent_txn"] - trend["early_txn"]
trend["txn_ratio"] = trend["recent_txn"] / trend["early_txn"].replace(0, np.nan)

df = df.merge(trend, on="customer_id", how="left")


# ============================================================
# 3. FEATURES (same as 06_model.py)
# ============================================================
df["age_group"] = pd.cut(df["age"], bins=[0, 30, 45, 60, 200],
                         labels=["under30", "30-44", "45-59", "60plus"])

features = ["monthly_logins", "num_products", "is_active_member", "age_group",
            "geography", "complaints_last_year", "tenure",
            "txn_change", "txn_ratio"]

X = pd.get_dummies(df[features], columns=["geography", "age_group"], drop_first=True)
y = df["exited"]


# ============================================================
# 4. OUT-OF-FOLD SCORES
# ============================================================
rf = RandomForestClassifier(n_estimators=100, class_weight="balanced",
                            random_state=42, n_jobs=-1)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print("Scoring 100k customers with 5-fold CV (takes a few minutes)...")
df["churn_probability"] = cross_val_predict(rf, X, y, cv=cv,
                                            method="predict_proba")[:, 1]

# Should land close to the 0.973 test-set AUC from 06_model.py
print("Out-of-fold ROC-AUC:", round(roc_auc_score(y, df["churn_probability"]), 4))


# ============================================================
# 5. RISK LEVEL AND EXPECTED LOSS
# ============================================================
df["risk_level"] = pd.cut(df["churn_probability"], bins=[0, 0.3, 0.6, 1.0],
                          labels=["Low", "Medium", "High"],
                          include_lowest=True).astype(str)

# Rank by what's actually at stake, not probability alone
df["customer_value"] = df["balance"] + df["estimated_salary"] * 0.1
df["expected_loss"] = df["churn_probability"] * df["customer_value"]

print("\nRisk level split (retained customers only):")
print(df.loc[df["exited"] == 0, "risk_level"].value_counts())


# ============================================================
# 6. SAVE TO MYSQL (for Power BI)
# ============================================================
scores = df[["customer_id", "churn_probability", "risk_level",
             "customer_value", "expected_loss"]]
scores.to_csv(OUTPUT_DIR / "churn_scores.csv", index=False)   # backup in case the DB save fails
scores.to_sql("churn_scores", get_engine(), if_exists="replace", index=False)
print("\nSaved churn_scores:", len(scores))


# ============================================================
# 7. CALL LIST: top 500 retained customers by expected loss
# ============================================================
call_list = (df[df["exited"] == 0]
             .sort_values("expected_loss", ascending=False)
             .head(500)
             [["customer_id", "geography", "churn_probability",
               "risk_level", "customer_value", "expected_loss"]])

call_list.to_csv(OUTPUT_DIR / "high_risk_customers.csv", index=False)
print(call_list.head(20).to_string(index=False))
print("Total value at risk (top 500):", round(call_list["expected_loss"].sum(), 2))