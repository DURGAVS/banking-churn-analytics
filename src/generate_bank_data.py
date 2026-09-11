"""
Synthetic Banking Dataset Generator
====================================
Creates a multi-table banking dataset for churn + credit risk analysis.

Tables produced:
    branches.csv           - 60 bank branches across regions
    products.csv           - 10 banking products
    customers.csv          - 100,000 customers (the main table)
    customer_products.csv  - which customer holds which product
    loans.csv              - loan accounts with default flags
    monthly_activity.csv   - 12 months of account activity per customer
    weekly_drops/          - incremental files for the automation pipeline

Deliberate data quality issues are planted so the cleaning step is real.
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
import os

RNG = np.random.default_rng(42)
N_CUSTOMERS = 100_000
OUT = "/home/claude/bank_data"
os.makedirs(OUT, exist_ok=True)
os.makedirs(f"{OUT}/weekly_drops", exist_ok=True)

START = date(2019, 1, 1)
TODAY = date(2026, 9, 1)


# ----------------------------------------------------------------------
# 1. BRANCHES
# ----------------------------------------------------------------------
countries = {
    "France":  ["Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes",
                "Strasbourg", "Bordeaux", "Lille", "Rennes"],
    "Germany": ["Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt",
                "Stuttgart", "Dusseldorf", "Leipzig", "Dortmund", "Essen"],
    "Spain":   ["Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza",
                "Malaga", "Bilbao", "Alicante", "Murcia", "Palma"],
}
regions = ["North", "South", "East", "West", "Central"]

branch_rows = []
bid = 1000
for country, cities in countries.items():
    for city in cities:
        for _ in range(2):          # 2 branches per city -> 60 total
            bid += 1
            branch_rows.append({
                "branch_id": bid,
                "branch_name": f"{city} {'Main' if bid % 2 == 0 else 'Central'}",
                "city": city,
                "country": country,
                "region": RNG.choice(regions),
                "opened_year": int(RNG.integers(1985, 2020)),
                "staff_count": int(RNG.integers(8, 45)),
            })
branches = pd.DataFrame(branch_rows)


# ----------------------------------------------------------------------
# 2. PRODUCTS
# ----------------------------------------------------------------------
products = pd.DataFrame([
    {"product_id": 1,  "product_name": "Savings Account",   "category": "Deposit",    "monthly_fee": 0.0,   "risk_weight": 0.0},
    {"product_id": 2,  "product_name": "Current Account",   "category": "Deposit",    "monthly_fee": 2.5,   "risk_weight": 0.0},
    {"product_id": 3,  "product_name": "Fixed Deposit",     "category": "Deposit",    "monthly_fee": 0.0,   "risk_weight": 0.0},
    {"product_id": 4,  "product_name": "Credit Card",       "category": "Credit",     "monthly_fee": 5.0,   "risk_weight": 0.6},
    {"product_id": 5,  "product_name": "Personal Loan",     "category": "Credit",     "monthly_fee": 0.0,   "risk_weight": 0.9},
    {"product_id": 6,  "product_name": "Home Loan",         "category": "Credit",     "monthly_fee": 0.0,   "risk_weight": 0.4},
    {"product_id": 7,  "product_name": "Auto Loan",         "category": "Credit",     "monthly_fee": 0.0,   "risk_weight": 0.7},
    {"product_id": 8,  "product_name": "Mutual Fund",       "category": "Investment", "monthly_fee": 1.5,   "risk_weight": 0.0},
    {"product_id": 9,  "product_name": "Insurance Plan",    "category": "Insurance",  "monthly_fee": 12.0,  "risk_weight": 0.0},
    {"product_id": 10, "product_name": "Locker Service",    "category": "Service",    "monthly_fee": 8.0,   "risk_weight": 0.0},
])


# ----------------------------------------------------------------------
# 3. CUSTOMERS
# ----------------------------------------------------------------------
n = N_CUSTOMERS
cust = pd.DataFrame({"customer_id": np.arange(100001, 100001 + n)})

# Geography: France largest, then Germany, then Spain
cust["geography"] = RNG.choice(["France", "Germany", "Spain"], n, p=[0.50, 0.27, 0.23])
cust["gender"] = RNG.choice(["Male", "Female"], n, p=[0.545, 0.455])

# Age: right-skewed, most customers 25-60
cust["age"] = np.clip(RNG.gamma(shape=9.0, scale=4.4, size=n) + 16, 18, 92).round().astype(int)

# Credit score: normal-ish, clipped to the usual 350-850 band
cust["credit_score"] = np.clip(RNG.normal(650, 97, n), 350, 850).round().astype(int)

# Tenure in years with the bank
cust["tenure"] = RNG.integers(0, 11, n)

# Join date derived from tenure (so the two agree)
join_offsets = (cust["tenure"] * 365 + RNG.integers(0, 365, n)).astype(int)
cust["join_date"] = [TODAY - timedelta(days=int(d)) for d in join_offsets]

# Balance: a large share hold zero balance (very common in retail banking)
has_balance = RNG.random(n) > 0.36
raw_balance = RNG.gamma(shape=6.0, scale=20000, size=n)
cust["balance"] = np.where(has_balance, raw_balance, 0).round(2)

# Estimated salary, loosely tied to age and credit score
cust["estimated_salary"] = np.clip(
    RNG.normal(95000, 42000, n)
    + (cust["age"] - 38) * 420
    + (cust["credit_score"] - 650) * 22,
    12000, 300000
).round(2)

# Number of products held
cust["num_products"] = RNG.choice([1, 2, 3, 4], n, p=[0.50, 0.44, 0.045, 0.015])

cust["has_cr_card"] = RNG.choice([0, 1], n, p=[0.29, 0.71])
cust["is_active_member"] = RNG.choice([0, 1], n, p=[0.48, 0.52])

# Branch assignment must respect the customer's country
branch_by_country = {c: branches.loc[branches.country == c, "branch_id"].values
                     for c in countries}
cust["branch_id"] = [int(RNG.choice(branch_by_country[g])) for g in cust["geography"]]

# Customer segment driven by balance and salary
seg_score = cust["balance"] / 1000 + cust["estimated_salary"] / 3000
cust["segment"] = pd.cut(
    seg_score,
    bins=[-1, 25, 55, 95, 1e9],
    labels=["Basic", "Standard", "Premium", "Wealth"]
).astype(str)

# Support complaints in the last year
complaint_rate = 0.13 + 0.10 * (cust["is_active_member"] == 0)
cust["complaints_last_year"] = RNG.binomial(3, complaint_rate)

# Digital engagement (logins per month) - lower for inactive members
cust["monthly_logins"] = np.clip(
    RNG.poisson(np.where(cust["is_active_member"] == 1, 11, 2.4)), 0, 60
)


# ----------------------------------------------------------------------
# 4. CHURN — built from a logistic model so relationships are testable
# ----------------------------------------------------------------------
logit = np.full(n, -2.95)

# Geography: Germany churns notably higher
logit += np.where(cust["geography"] == "Germany", 0.88, 0.0)
logit += np.where(cust["geography"] == "Spain", 0.05, 0.0)

# Gender
logit += np.where(cust["gender"] == "Female", 0.34, 0.0)

# Age: risk climbs into the 45-60 band then eases off
age_effect = -0.0016 * (cust["age"] - 50) ** 2 + 1.05
logit += np.clip(age_effect, -1.2, 1.05)

# Activity
logit += np.where(cust["is_active_member"] == 0, 0.82, -0.22)

# Number of products: 2 is the sweet spot, 3-4 is a red flag
prod_effect = {1: 0.42, 2: -0.35, 3: 2.15, 4: 2.95}
logit += cust["num_products"].map(prod_effect).values

# Tenure: longer relationships are stickier
logit += -0.048 * cust["tenure"]

# Credit score: weak but real negative relationship
logit += -0.0014 * (cust["credit_score"] - 650)

# Zero-balance customers churn slightly less (often dormant, not leaving)
logit += np.where(cust["balance"] == 0, -0.28, 0.0)

# Complaints
logit += 0.44 * cust["complaints_last_year"]

# Digital engagement
logit += -0.030 * cust["monthly_logins"]

# Segment
seg_effect = {"Basic": 0.18, "Standard": 0.0, "Premium": -0.12, "Wealth": -0.30}
logit += cust["segment"].map(seg_effect).values

prob = 1 / (1 + np.exp(-logit))
cust["exited"] = (RNG.random(n) < prob).astype(int)

# Churn date for those who left (needed for trend analysis)
churn_dates = []
for exited, jd in zip(cust["exited"], cust["join_date"]):
    if exited == 0:
        churn_dates.append(pd.NaT)
    else:
        span = (TODAY - jd).days
        offset = int(RNG.integers(max(30, int(span * 0.25)), max(31, span)))
        churn_dates.append(jd + timedelta(days=offset))
cust["churn_date"] = churn_dates

# Surnames for realism
surnames = ["Hargrave","Hill","Onio","Boni","Mitchell","Chu","Bartlett","Obinna",
            "Ferri","Andrews","Kay","Chin","Scott","Goforth","Romeo","Henderson",
            "Muller","Schmidt","Weber","Fischer","Garcia","Lopez","Martinez",
            "Sanchez","Dubois","Moreau","Laurent","Simon","Michel","Bernard",
            "Rossi","Costa","Silva","Santos","Pereira","Alves","Klein","Wolf",
            "Neumann","Braun","Ferrari","Russo","Greco","Bruno","Gallo"]
cust["surname"] = RNG.choice(surnames, n)

cust = cust[["customer_id","surname","geography","gender","age","credit_score",
             "tenure","join_date","balance","estimated_salary","num_products",
             "has_cr_card","is_active_member","branch_id","segment",
             "complaints_last_year","monthly_logins","exited","churn_date"]]


# ----------------------------------------------------------------------
# 5. CUSTOMER_PRODUCTS — one row per product held
# ----------------------------------------------------------------------
cp_rows = []
prod_ids = products["product_id"].values
# Deposit products are far more common than credit/investment ones
prod_weights = np.array([0.22,0.20,0.09,0.16,0.07,0.05,0.06,0.06,0.05,0.04])
prod_weights = prod_weights / prod_weights.sum()

for cid, k, jd, exited, cdate in zip(cust["customer_id"], cust["num_products"],
                                     cust["join_date"], cust["exited"],
                                     cust["churn_date"]):
    chosen = RNG.choice(prod_ids, size=k, replace=False, p=prod_weights)
    for pid in chosen:
        span = max(1, (TODAY - jd).days)
        opened = jd + timedelta(days=int(RNG.integers(0, span)))
        if exited == 1 and pd.notna(cdate) and RNG.random() < 0.8:
            closed, status = cdate, "Closed"
        else:
            closed, status = pd.NaT, "Active"
        cp_rows.append((cid, int(pid), opened, closed, status))

customer_products = pd.DataFrame(
    cp_rows, columns=["customer_id","product_id","opened_date","closed_date","status"]
)


# ----------------------------------------------------------------------
# 6. LOANS — the credit risk half of the project
# ----------------------------------------------------------------------
loan_holders = customer_products[customer_products.product_id.isin([5, 6, 7])]
loan_holders = loan_holders.merge(
    cust[["customer_id","credit_score","estimated_salary","age","exited"]],
    on="customer_id"
)
m = len(loan_holders)

loan_type_map = {5: "Personal", 6: "Home", 7: "Auto"}
amounts = {"Personal": (5000, 60000), "Home": (60000, 600000), "Auto": (8000, 70000)}
terms   = {"Personal": [12,24,36,48,60], "Home": [120,180,240,300,360], "Auto": [24,36,48,60,72]}

loan_type = loan_holders["product_id"].map(loan_type_map).values
lo = np.array([amounts[t][0] for t in loan_type])
hi = np.array([amounts[t][1] for t in loan_type])
loan_amount = (RNG.random(m) * (hi - lo) + lo).round(2)

# Interest rate falls as credit score rises
interest = np.clip(
    16.5 - 0.011 * (loan_holders["credit_score"].values - 350) + RNG.normal(0, 1.1, m),
    3.2, 24.0
).round(2)

term = np.array([int(RNG.choice(terms[t])) for t in loan_type])
monthly_payment = (loan_amount * (interest/100/12) /
                   (1 - (1 + interest/100/12) ** (-term))).round(2)

# Debt-to-income ratio
dti = np.clip(monthly_payment * 12 / loan_holders["estimated_salary"].values, 0.01, 3.0).round(3)

credit_util = np.clip(
    RNG.beta(2.2, 3.4, m) + 0.30 * (dti > 0.42) - 0.0009 * (loan_holders["credit_score"].values - 650),
    0.0, 1.0
).round(3)

missed = RNG.poisson(
    np.clip(0.30 + 1.5 * dti + 1.1 * credit_util - 0.0035 * (loan_holders["credit_score"].values - 350), 0.05, 6)
)

# Default probability
d_logit = (-4.55
           + 2.4 * dti
           + 1.6 * credit_util
           + 0.42 * missed
           - 0.0052 * (loan_holders["credit_score"].values - 650)
           + 0.35 * loan_holders["exited"].values)
default_flag = (RNG.random(m) < 1/(1+np.exp(-d_logit))).astype(int)

loans = pd.DataFrame({
    "loan_id": np.arange(500001, 500001 + m),
    "customer_id": loan_holders["customer_id"].values,
    "loan_type": loan_type,
    "loan_amount": loan_amount,
    "interest_rate": interest,
    "term_months": term,
    "monthly_payment": monthly_payment,
    "debt_to_income": dti,
    "credit_utilization": credit_util,
    "missed_payments_12m": missed,
    "loan_status": np.where(default_flag == 1, "Default",
                   np.where(RNG.random(m) < 0.22, "Closed", "Active")),
    "default_flag": default_flag,
    "disbursed_date": loan_holders["opened_date"].values,
})


# ----------------------------------------------------------------------
# 7. MONTHLY ACTIVITY — 12 months, for window-function practice
# ----------------------------------------------------------------------
months = pd.date_range("2025-09-01", periods=12, freq="MS")
act = []
base_txn = np.where(cust["is_active_member"] == 1, 18, 4)

for i, mth in enumerate(months):
    decay = 1.0 - (cust["exited"].values * 0.055 * i)   # leavers wind down
    txn = np.clip(RNG.poisson(np.clip(base_txn * decay, 0.4, None)), 0, 120)
    debit = (txn * RNG.gamma(2.4, 55, n)).round(2)
    credit = (debit * RNG.normal(1.03, 0.22, n)).clip(0).round(2)
    avg_bal = (cust["balance"].values * RNG.normal(1.0, 0.09, n) * decay).clip(0).round(2)
    act.append(pd.DataFrame({
        "customer_id": cust["customer_id"].values,
        "activity_month": mth.date(),
        "num_transactions": txn,
        "total_debit": debit,
        "total_credit": credit,
        "avg_balance": avg_bal,
    }))
monthly_activity = pd.concat(act, ignore_index=True)


# ----------------------------------------------------------------------
# 8. PLANT DATA QUALITY ISSUES  (so the cleaning step is genuine work)
# ----------------------------------------------------------------------
dirty = cust.copy()

# a) inconsistent gender labels
idx = RNG.choice(n, int(n * 0.08), replace=False)
dirty.loc[idx, "gender"] = dirty.loc[idx, "gender"].map({"Male": "M", "Female": "F"})
idx = RNG.choice(n, int(n * 0.04), replace=False)
dirty.loc[idx, "gender"] = dirty.loc[idx, "gender"].str.lower()

# b) missing values
for col, frac in [("credit_score", 0.021), ("estimated_salary", 0.017),
                  ("age", 0.009), ("monthly_logins", 0.013)]:
    dirty.loc[RNG.choice(n, int(n * frac), replace=False), col] = np.nan

# c) whitespace and case noise in geography
idx = RNG.choice(n, int(n * 0.05), replace=False)
dirty.loc[idx, "geography"] = " " + dirty.loc[idx, "geography"] + " "
idx = RNG.choice(n, int(n * 0.02), replace=False)
dirty.loc[idx, "geography"] = dirty.loc[idx, "geography"].str.upper()

# d) balance stored as text with currency symbols on some rows
dirty["balance"] = dirty["balance"].astype(str)
idx = RNG.choice(n, int(n * 0.06), replace=False)
dirty.loc[idx, "balance"] = "€" + dirty.loc[idx, "balance"]

# e) duplicate rows
dupes = dirty.sample(650, random_state=7)
dirty = pd.concat([dirty, dupes], ignore_index=True)

# f) a few impossible ages
idx = RNG.choice(len(dirty), 90, replace=False)
dirty.loc[idx, "age"] = RNG.choice([0, 1, 3, 199, 250], 90)

dirty = dirty.sample(frac=1, random_state=11).reset_index(drop=True)


# ----------------------------------------------------------------------
# 9. WEEKLY DROP FILES — for the automation pipeline
# ----------------------------------------------------------------------
shuffled = dirty.sample(frac=1, random_state=3).reset_index(drop=True)
n_chunks = 8
size = int(np.ceil(len(shuffled) / n_chunks))
chunks = [shuffled.iloc[i*size:(i+1)*size] for i in range(n_chunks)]
for i, ch in enumerate(chunks, start=1):
    ch.to_csv(f"{OUT}/weekly_drops/customers_week_{i:02d}.csv", index=False)


# ----------------------------------------------------------------------
# 10. WRITE EVERYTHING
# ----------------------------------------------------------------------
branches.to_csv(f"{OUT}/branches.csv", index=False)
products.to_csv(f"{OUT}/products.csv", index=False)
dirty.to_csv(f"{OUT}/customers_raw.csv", index=False)
cust.to_csv(f"{OUT}/customers_clean_ANSWER_KEY.csv", index=False)
customer_products.to_csv(f"{OUT}/customer_products.csv", index=False)
loans.to_csv(f"{OUT}/loans.csv", index=False)
monthly_activity.to_csv(f"{OUT}/monthly_activity.csv.gz", index=False, compression="gzip")

print("=" * 62)
print("GENERATED")
print("=" * 62)
for f in sorted(os.listdir(OUT)):
    p = f"{OUT}/{f}"
    if os.path.isfile(p):
        print(f"  {f:42s} {os.path.getsize(p)/1e6:7.2f} MB")
print(f"  weekly_drops/ ......................... {len(chunks)} files")

print("\n" + "=" * 62)
print("SANITY CHECKS  (clean version)")
print("=" * 62)
print(f"Customers:            {len(cust):,}")
print(f"Overall churn rate:   {cust.exited.mean():.1%}")
print(f"Loans:                {len(loans):,}   default rate {loans.default_flag.mean():.1%}")
print(f"Product holdings:     {len(customer_products):,}")
print(f"Activity rows:        {len(monthly_activity):,}")
print(f"\nChurn by geography:\n{cust.groupby('geography').exited.mean().round(3)}")
print(f"\nChurn by num_products:\n{cust.groupby('num_products').exited.mean().round(3)}")
print(f"\nChurn by active member:\n{cust.groupby('is_active_member').exited.mean().round(3)}")
print(f"\nMean credit score  churned vs stayed:")
print(cust.groupby('exited').credit_score.mean().round(1))
print(f"\nMean tenure  churned vs stayed:")
print(cust.groupby('exited').tenure.mean().round(2))
