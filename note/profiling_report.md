# Data Profiling Report

## Summary

I profiled the banking dataset to understand the data quality before starting the main analysis. I checked the customers, loans, and customer_products tables and also checked the relationships between the tables.

Most of the issues were found in the customers table. These included duplicate customer records, invalid ages, inconsistent geography and gender values, balance formatting issues, missing values, and future-dated churn records.

One important finding was customer ID 117688. Although there are 650 duplicate customer IDs in total, 649 of them are exact copies. Customer 117688 is different because the two records contain different ages: 51 and 250. This means it needs to be handled as a data conflict rather than as a simple duplicate.

## Tables Profiled

| Table             |      Rows | Status       |
| ----------------- | --------: | ------------ |
| customers         |   100,650 | Issues found |
| loans             |    29,466 | Profiled     |
| customer_products |   157,299 | Profiled     |
| branches          |        60 | Profiled     |
| products          |        10 | Profiled     |
| monthly_activity  | 1,200,000 | Profiled     |

## Issues Found

### 1. Duplicate customer records

I found 650 duplicate customer IDs in the customers table.

Of these, 649 are exact copies of the same customer record, so they can be removed as duplicates.

The remaining duplicate is customer ID 117688. This customer appears twice, but the two records have different ages: one record has age 51 and the other has age 250.

Since 250 is an invalid age, I will first replace the invalid age with a null value. After handling the invalid age, the two records can be compared properly. The record with age 51 will be kept because it contains the valid customer information.

The order of these steps matters. Invalid ages need to be handled before deduplication. Otherwise, the two records for customer 117688 would not look like duplicates because their age values are different.

### 2. Invalid customer ages

I found 37 customers with an age above 100 and 53 customers with an age below 18. This gives 90 records with invalid ages.

These values could affect analysis based on customer age.

I will replace invalid ages with null values rather than guessing the correct age. The duplicate records will then be handled, including the conflict for customer 117688. After deduplication, the missing age values will be filled using the median age.

Age cleaning will happen before deduplication so that invalid values do not hide duplicate or conflicting records.

### 3. Inconsistent geography values

The geography column contains 12 distinct values even though the expected values are only France, Germany, and Spain.

The differences are caused by extra spaces and inconsistent capitalization. For example, France appears as `France`, ` France`, and `FRANCE`.

A GROUP BY on geography would return 12 groups instead of 3, splitting each country's figures across multiple rows with no error raised.

I will standardize these values to:

* France
* Germany
* Spain

### 4. Inconsistent gender values

The gender column contains 8 distinct values even though only two standard categories are expected.

The different formats need to be standardized so that the same category is not treated as multiple categories during analysis.

If gender values are not standardized, GROUP BY and filtering could split the same category into separate groups and produce incorrect counts and comparisons.

### 5. Balance formatting issue

Some balance values contain currency symbols such as `€`, which can cause the column to be treated as text instead of a number.

If the balance remains as text, calculations such as SUM, AVG, and other financial analysis may not work correctly or may require additional conversion each time.

I will remove the currency symbols and convert the balance column to a proper numeric data type so it can be used correctly in calculations and analysis.

### 6. Missing values

Missing values were found in four columns:

| Column           | Missing percentage |
| ---------------- | -----------------: |
| age              |              0.89% |
| credit_score     |              2.10% |
| estimated_salary |              1.70% |
| monthly_logins   |              1.30% |

Missing values can reduce the number of records available for calculations and can affect averages, comparisons, and other analysis if they are not handled properly.

For age, invalid values will first be changed to null. The duplicate records will then be handled, and the resulting missing age values will be filled using the median age.

The other missing values will be handled according to the meaning of each column rather than applying the same method to every column.

### 7. Future churn dates beyond the data snapshot

**What I found:** The data snapshot date was 1 September 2026, but 181 customers had a churn date on or after the snapshot date. Of these, 7 customers churned exactly on 1 September 2026. These records were valid because customers also joined on that date, making it part of the observed data period. However, the remaining 174 customers had churn dates after the snapshot date, which is impossible because the data only describes the bank up to 1 September 2026.

This issue was not detected by the row-level checks. It became apparent when visualizing the monthly churn trend in Power BI, where a sudden cliff appeared at the end of the trend: churn dropped from 1,115 in August 2026 to just 175 in September and 6 in October. This demonstrated how visualizing the data caught a problem that the initial row-level checks had missed.

**Why it matters:** These 174 customers were incorrectly counted as churned even though they were still customers as of the snapshot date. This inflated the overall churn rate to 19.49%. The corrected rate is 19.32%.

The issue also distorted the tenure hypothesis result, with the effect size decreasing from Cohen's d = 0.111 to d = 0.094 after correction. All 174 incorrectly marked churners had joined in August 2026 and had a tenure of 0. These brand-new customers were incorrectly classified as churned, making tenure-0 customers appear riskier than they actually were and exaggerating the relationship between tenure and churn.

**How I handled it:** In `02_clean.py`, after deduplication, I set `exited = 0` and `churn_date = null` for the 174 customers whose churn dates fell after 1 September 2026. I retained the customer records because they represented real customers; only their churn information was incorrect. The 7 customers who churned exactly on the snapshot date were kept unchanged because those dates were valid within the observed data period.

## Checks Passed

The following checks did not show any major issues:

* Loan amounts do not contain zero or negative values.
* There are no duplicate loan IDs.
* The loans table does not contain null values.
* Loan status is consistent with the default flag.
* The number of products linked to each customer matches the `num_products` value in the customers table.
* No orphan foreign keys were found in the relationship checks performed.
* Missing `churn_date` values are expected for customers who have not churned.
  **Note:** This check only looked for missing `churn_date` values; it did not validate whether existing dates were valid relative to the 1 September 2026 snapshot. Consequently, it did not catch the 174 future-dated churn records. The issue was identified later through the monthly churn trend visualization in Power BI (see issue #7).

## Cleaning Plan

1. Identify invalid ages and replace them with null values.
2. Standardize geography and gender values.
3. Remove currency symbols from balance and convert it to a numeric data type.
4. Remove the 649 exact duplicate customer records and keep the cleaner record for customer 117688.
5. Correct future churn dates: reset the 174 churn records dated after the snapshot date by setting `exited = 0` and `churn_date = null`. Retain the customer rows because these are real customers. Keep the 7 valid churn records dated exactly 1 September 2026 unchanged.
6. Fill the missing age values using the median age.
7. Handle the remaining missing values according to the meaning of each column.
8. Run the profiling checks again after cleaning.
9. Validate the relationships between the tables again.
10. Create clean analytical tables for SQL analysis and dashboards.

## Limitations

Some loans have a debt-to-income value capped at 3.00, so the actual value for those records may be higher than the recorded value.

Also, an active loan may default in the future. Therefore, the current `default_flag` may not represent all future credit risk.

The products and monthly_activity tables have not yet been fully profiled, so I have not marked them as clean.