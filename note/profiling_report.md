# Data Profiling Report

## Summary

I profiled the banking dataset to understand the data quality before starting the main analysis. I checked the customers, loans, and customer_products tables and also checked the relationships between the tables.

Most of the issues were found in the customers table. These included duplicate customer records, invalid ages, inconsistent geography and gender values, balance formatting issues, and missing values.

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

## Checks Passed

The following checks did not show any major issues:

* Loan amounts do not contain zero or negative values.
* There are no duplicate loan IDs.
* The loans table does not contain null values.
* Loan status is consistent with the default flag.
* The number of products linked to each customer matches the `num_products` value in the customers table.
* No orphan foreign keys were found in the relationship checks performed.
* Missing `churn_date` values are expected for customers who have not churned.

## Cleaning Plan

1. Identify invalid ages and replace them with null values.
2. Standardize geography and gender values.
3. Remove currency symbols from balance and convert it to a numeric data type.
4. Remove the 649 exact duplicate customer records and keep the cleaner record for customer 117688.
5. Fill the missing age values using the median age.
6. Handle the remaining missing values according to the meaning of each column.
7. Run the profiling checks again after cleaning.
8. Validate the relationships between the tables again.
9. Create clean analytical tables for SQL analysis and dashboards.

## Limitations

Some loans have a debt-to-income value capped at 3.00, so the actual value for those records may be higher than the recorded value.

Also, an active loan may default in the future. Therefore, the current `default_flag` may not represent all future credit risk.

The products and monthly_activity tables have not yet been fully profiled, so I have not marked them as clean.
