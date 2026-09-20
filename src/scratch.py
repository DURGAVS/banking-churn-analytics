import pandas as pd

df = pd.read_csv("data/raw/customers_raw.csv")

churned = df[df["exited"] == 1]

print("Total customers:", len(df))
print("Churned customers:", len(churned))
print("Churned with no date:", churned["churn_date"].isna().sum())

print("Age above 100:", len(df[df["age"] > 100]))
print("Age below 18:", len(df[df["age"] < 18]))

print("Exact duplicates:", df.duplicated().sum())

print("Duplicate IDs:", df.duplicated(subset=["customer_id"]).sum())

dupes = df[df.duplicated(subset=["customer_id"], keep=False)]
print(dupes.sort_values("customer_id").head(20))

g = dupes.groupby("customer_id").nunique()
print(g[g.max(axis=1) > 1])

print(df[df["customer_id"] == 117688])

print(df.columns.tolist())


# ==========================================
# LOANS TABLE
# ==========================================

loans = pd.read_csv("data/raw/loans.csv")

print("\nLOAN ANALYSIS")

print("Negative loan amounts:", len(loans[loans["loan_amount"] < 0]))
print("Negative interest rates:", len(loans[loans["interest_rate"] < 0]))
print("Negative monthly payments:", len(loans[loans["monthly_payment"] < 0]))
print("Duplicate loan IDs:", loans.duplicated(subset=["loan_id"]).sum())

print("loan amount is zero:",len(loans[loans["loan_amount"] == 0]))
print("\nDefault flag:")
print(loans["default_flag"].value_counts())
print(pd.crosstab(loans["loan_status"], loans["default_flag"]))


print("debt_to_income :",len(loans[loans["debt_to_income"] == 3.00]))


# ==========================================
#product
# ==========================================

import pandas as pd

customers = pd.read_csv("data/raw/customers_raw.csv")
customer_products = pd.read_csv("data/raw/customer_products.csv")

# Count products for each customer
product_counts = (
    customer_products
    .groupby("customer_id")
    .size()
    .reset_index(name="actual_product_count")
)

# Compare with customers.num_products
check = customers[
    ["customer_id", "num_products"]
].merge(
    product_counts,
    on="customer_id",
    how="left"
)

# Customers with no matching product rows
check["actual_product_count"] = check["actual_product_count"].fillna(0)

# Find mismatches
mismatches = check[
    check["num_products"] != check["actual_product_count"]
]

print(mismatches)


product_counts = (
    customer_products
    .groupby("customer_id")
    .size()
    .reset_index(name="actual_product_count")
)
print(product_counts)




print("Duplicate customer IDs:", customers.duplicated(subset=["customer_id"]).sum())

print("Age above 100:", len(customers[customers["age"] > 100]))
print("Age below 18:", len(customers[customers["age"] < 18]))

print("Geography values:")
print(customers["geography"].value_counts())

print("Gender values:")
print(customers["gender"].value_counts())

activity = pd.read_csv("data/raw/monthly_activity.csv")
counts = activity.groupby("customer_id").size()
print(counts.value_counts())

print((activity["total_debit"] < 0).sum())
print((activity["total_credit"] < 0).sum())
print((activity["avg_balance"] < 0).sum())


loans = pd.read_csv("data/raw/loans.csv")
print(loans.columns.tolist())

activity = pd.read_csv("data/raw/monthly_activity.csv")
print(activity.columns.tolist())