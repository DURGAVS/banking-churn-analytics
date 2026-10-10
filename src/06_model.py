import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.ensemble import RandomForestClassifier


# ============================================================
# 1. LOAD DATA
# ============================================================

df = pd.read_csv("data/processed/customers_clean.csv")

activity = pd.read_csv("data/raw/monthly_activity.csv")
activity = activity.sort_values(["customer_id", "activity_month"])


# ============================================================
# 2. BUILD TREND FEATURES
# ============================================================

# First 3 months and last 3 months per customer

first3 = (
    activity
    .groupby("customer_id")
    .head(3)
    .groupby("customer_id")
    .agg(
        early_txn=("num_transactions", "mean")
    )
)

last3 = (
    activity
    .groupby("customer_id")
    .tail(3)
    .groupby("customer_id")
    .agg(
        recent_txn=("num_transactions", "mean")
    )
)

trend = first3.join(last3)

trend["txn_change"] = (
    trend["recent_txn"] - trend["early_txn"]
)

trend["txn_ratio"] = (
    trend["recent_txn"]
    / trend["early_txn"].replace(0, np.nan)
)

print("Trend features:")
print(trend.head())
print("Trend rows:", len(trend))


# ============================================================
# 3. MERGE TREND FEATURES
# ============================================================

df = df.merge(
    trend,
    on="customer_id",
    how="left"
)


# Check for missing trend values
print("Missing txn_change:", df["txn_change"].isna().sum())
print("Missing txn_ratio:", df["txn_ratio"].isna().sum())


# ============================================================
# 4. CREATE AGE GROUP
# ============================================================

df["age_group"] = pd.cut(
    df["age"],
    bins=[0, 30, 45, 60, 200],
    labels=["under30", "30-44", "45-59", "60plus"]
)


# ============================================================
# 5. SELECT FEATURES
# ============================================================

# Features selected from Phase 4 effect sizes.
# churn_date is deliberately excluded — only churners have one,
# so including it would leak the answer into the model.

features = [
    "monthly_logins",
    "num_products",
    "is_active_member",
    "age_group",
    "geography",
    "complaints_last_year",
    "tenure",
    "txn_change",
    "txn_ratio"
]

X = df[features]
y = df["exited"]


# ============================================================
# 6. BASIC CHECKS
# ============================================================

print("Rows:", len(X))
print("Churn rate:", round(y.mean(), 4))
print(X.dtypes)


# ============================================================
# 7. ENCODE CATEGORICAL FEATURES
# ============================================================

X = pd.get_dummies(
    X,
    columns=["geography", "age_group"],
    drop_first=True
)

print("Features after encoding:")
print(X.columns.tolist())


# ============================================================
# 8. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(
    "Train:",
    len(X_train),
    "churn rate:",
    round(y_train.mean(), 4)
)

print(
    "Test: ",
    len(X_test),
    "churn rate:",
    round(y_test.mean(), 4)
)


# ============================================================
# 9. SCALE FEATURES FOR LOGISTIC REGRESSION
# ============================================================

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


# ============================================================
# 10. TRAIN LOGISTIC REGRESSION
# ============================================================

model = LogisticRegression(
    max_iter=1000,
    class_weight="balanced"
)

model.fit(
    X_train_scaled,
    y_train
)

print("Model trained")


# ============================================================
# 11. EVALUATE LOGISTIC REGRESSION
# ============================================================

y_pred = model.predict(X_test_scaled)

y_prob = model.predict_proba(X_test_scaled)[:, 1]

print(
    "Accuracy:",
    round((y_pred == y_test).mean(), 4)
)

print()

print("Confusion matrix:")
print(confusion_matrix(y_test, y_pred))

print()

print(
    classification_report(
        y_test,
        y_pred,
        digits=3
    )
)

print(
    "ROC-AUC:",
    round(
        roc_auc_score(y_test, y_prob),
        4
    )
)


# ============================================================
# 12. THRESHOLD ANALYSIS
# ============================================================

print()
print("=== THRESHOLD ANALYSIS ===")

for t in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:

    pred = (y_prob >= t).astype(int)

    flagged = pred.sum()

    caught = (
        (pred == 1) &
        (y_test == 1)
    ).sum()

    precision = (
        caught / flagged
        if flagged
        else 0
    )

    recall = (
        caught / y_test.sum()
    )

    print(
        f"{t:.2f}  "
        f"flagged={flagged:6d}  "
        f"caught={caught:5d}  "
        f"precision={precision:.3f}  "
        f"recall={recall:.3f}"
    )


# ============================================================
# 13. TRAIN RANDOM FOREST
# ============================================================

rf = RandomForestClassifier(
    n_estimators=100,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

rf.fit(
    X_train,
    y_train
)


# ============================================================
# 14. EVALUATE RANDOM FOREST
# ============================================================

rf_prob = rf.predict_proba(X_test)[:, 1]

rf_pred = rf.predict(X_test)

print()
print("=== RANDOM FOREST ===")

print(
    classification_report(
        y_test,
        rf_pred,
        digits=3
    )
)

print(
    "ROC-AUC:",
    round(
        roc_auc_score(y_test, rf_prob),
        4
    )
)


# ============================================================
# 15. RANDOM FOREST FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame({
    "feature": X_train.columns,
    "importance": rf.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

print()
print("=== FEATURE IMPORTANCE ===")
print(importance)


# ============================================================
# 16. LOGISTIC REGRESSION COEFFICIENTS
# ============================================================

coefs = pd.DataFrame({
    "feature": X_train.columns,
    "coefficient": model.coef_[0]
}).sort_values(
    "coefficient",
    ascending=False
)

print()
print("=== LOGISTIC COEFFICIENTS ===")
print(coefs)


print(df.groupby("exited")[["txn_ratio", "txn_change"]].mean())



df["churn_date"] = pd.to_datetime(df["churn_date"])

before = df[(df["exited"] == 1) & (df["churn_date"] < "2025-09-01")]
during = df[(df["exited"] == 1) & (df["churn_date"] >= "2025-09-01")]

print("Churned BEFORE activity window:", len(before))
print("  mean txn_ratio:", round(before["txn_ratio"].mean(), 3))

print("Churned DURING activity window:", len(during))
print("  mean txn_ratio:", round(during["txn_ratio"].mean(), 3))


# Score every customer
df["churn_probability"] = rf.predict_proba(X)[:, 1]

df["risk_level"] = pd.cut(df["churn_probability"],
                          bins=[0, 0.3, 0.6, 1.0],
                          labels=["Low", "Medium", "High"])

# Rank by what's actually at stake, not probability alone
df["customer_value"] = df["balance"] + df["estimated_salary"] * 0.1
df["expected_loss"] = df["churn_probability"] * df["customer_value"]

call_list = (df[df["exited"] == 0]
             .sort_values("expected_loss", ascending=False)
             .head(500)
             [["customer_id", "geography", "churn_probability",
               "risk_level", "customer_value", "expected_loss"]])

call_list.to_csv("outputs/high_risk_customers.csv", index=False)

print(call_list.head(20))
print("Total value at risk:", round(call_list["expected_loss"].sum(), 2))



# Score every customer
df["churn_probability"] = rf.predict_proba(X)[:, 1]

df["risk_level"] = pd.cut(df["churn_probability"],
                          bins=[0, 0.3, 0.6, 1.0],
                          labels=["Low", "Medium", "High"])

# Rank by what's actually at stake, not probability alone
df["customer_value"] = df["balance"] + df["estimated_salary"] * 0.1
df["expected_loss"] = df["churn_probability"] * df["customer_value"]

call_list = (df[df["exited"] == 0]
             .sort_values("expected_loss", ascending=False)
             .head(500)
             [["customer_id", "geography", "churn_probability",
               "risk_level", "customer_value", "expected_loss"]])

call_list.to_csv("outputs/high_risk_customers.csv", index=False)

print(call_list.head(20))
print("Total value at risk:", round(call_list["expected_loss"].sum(), 2))
print("  mean txn_ratio:", round(during["txn_ratio"].mean(), 3))