#making ages(below 18 or above 100) to null for perfect median caluclation and to voide those values
# Ages of 0, 1, 250 etc. are impossible. Set to null rather than deleting
# the row, since the other columns in those rows are valid.
# Nulls are filled with the median later, after deduplication.

import pandas as pd
import numpy as np
df = pd.read_csv("data/raw/customers_raw.csv")
print("Rows at start:", len(df))
print("Age nulls before:", df["age"].isna().sum())
df.loc[(df["age"]>100) | (df["age"]<18),"age"] =np.nan
print("Age nulls after:", df["age"].isna().sum())

# removing whitespaces and making titls case and cleaning the formate 
# geography had 12 distinct values instead of 3, caused by stray whitespace
# (" France ") and inconsistent case ("FRANCE"). A GROUP BY would silently
# return 12 country groups, splitting each country's churn rate.
print("geography before:",df["geography"].nunique())
df["geography"]=df["geography"].str.strip().str.title()
print("geography after:",df["geography"].nunique())
print(df["geography"].unique())


print("gender before:",df["gender"].nunique())
df["gender"]=df["gender"].str.strip().str.title()
df["gender"]=df["gender"].replace({"M":"Male","F":"Female"})
print("Gender:",df["gender"].unique())
print("Gender after:",df["gender"].nunique())


#changing data type
print("balance dtype before:",df["balance"].dtype)
df["balance"]=df["balance"].str.replace('€','')
df["balance"]=pd.to_numeric(df["balance"])
print("balance dtype after:",df["balance"].dtype)


#Find duplicates → compare their quality → keep the cleanest row → remove the rest.
print("rows before dedup:",len(df))
df["_null_count"]=df.isna().sum(axis=1)
df = df.sort_values("_null_count")
df = df.drop_duplicates(subset=["customer_id"],keep="first")
df=df.drop(columns="_null_count")
print("Rows after dedup:", len(df))
print(df[df["customer_id"] == 117688][["customer_id", "age"]])


##filling missing ages values with median age
print("before filln age:",df["age"].isna().sum())
df["age_was_missing"]=df["age"].isna().astype(int)
median_age=df["age"].median()
df["age"]=df["age"].fillna(median_age)
print("Median_age_used:",median_age)
print("after filln age:",df["age"].isna().sum())
print(df["age"].describe())


# filling missing credit score with median credit score
print("before_fill_credit_null:",df["credit_score"].isna().sum())
df["missing_credit_score"]=df["credit_score"].isna().astype(int)
median_credit_score=df["credit_score"].median()
df["credit_score"]=df["credit_score"].fillna(median_credit_score)
print("median_credit_score:",median_credit_score)
print("after_fill_in_with_median_null:",df["credit_score"].isna().sum())


#nulls filling with median estimated salary
print("Null_before_filling_estimated_salary:",df["estimated_salary"].isna().sum())
df["missing_estimated_salary"]=df["estimated_salary"].isna().astype(int)
median_estimated_salary=df["estimated_salary"].median()
df["estimated_salary"]=df["estimated_salary"].fillna(median_estimated_salary)
print("median_estimate_salary:",median_estimated_salary)
print("After_filling_median:",df["estimated_salary"].isna().sum())




missing = df[df["monthly_logins"].isna()]

print("Missing-login customers:")
print(missing["is_active_member"].value_counts(normalize=True))

print("\nAll customers:")
print(df["is_active_member"].value_counts(normalize=True))

# monthly_logins nulls are randomly distributed — the active/inactive split
# among missing-login customers (50.5/49.5) matches the overall population
# (52/48). No evidence that blank means "never logged in", so median is
# used rather than 0.


print("before_filling_median_in_monthly_logins:",df["monthly_logins"].isna().sum())
median=df["monthly_logins"].median()
df["monthly_logins"]=df["monthly_logins"].fillna(median)
print("aafter_filling_median_logins:",df["monthly_logins"].isna().sum())


print(df.isna().sum())

df.to_csv("data/processed/customers_clean.csv", index=False)
print("Saved:", len(df), "rows")

answer = pd.read_csv(r"C:\Users\Durga\OneDrive\Documents\project2 unwanted\customers_clean_ANSWER_KEY.csv")
print("Mine:", len(df), " Answer:", len(answer))



print("Churn rate — mine:", df["exited"].mean().round(4))
print("Churn rate — answer:", answer["exited"].mean().round(4))

print("\nGeography — mine:")
print(df["geography"].value_counts())
print("\nGeography — answer:")
print(answer["geography"].value_counts())

print("\nMean credit score — mine:", df["credit_score"].mean().round(2))
print("Mean credit score — answer:", answer["credit_score"].mean().round(2))

print("Std — mine:", df["credit_score"].std().round(2))
print("Std — answer:", answer["credit_score"].std().round(2))

print("all null:",df.isna().sum())