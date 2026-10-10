# Hypothesis Testing Results

## Method

* **t-test** was used for continuous variables.
* **Chi-square test** was used for categorical variables.
* Both **p-value** and **effect size** were reported because the dataset has **100,000 customers**. A large sample can make very small differences statistically significant, so effect size helps measure practical importance.

## Results

| Variable         | Test       | p-value | Effect Size | Strength   | Key Finding                             |
| ---------------- | ---------- | ------: | ----------: | ---------- | --------------------------------------- |
| monthly_logins   | t-test     |  <0.001 |   d = 0.529 | Medium     | Strongest relationship with churn       |
| num_products     | Chi-square |  <0.001 |   V = 0.265 | Modest     | Product count strongly differs by churn |
| is_active_member | Chi-square |  <0.001 |   V = 0.230 | Modest     | Active members have lower churn         |
| age              | t-test     |  <0.001 |   d = 0.213 | Small      | Some association with churn             |
| geography        | Chi-square |  <0.001 |   V = 0.134 | Small      | Germany has much higher churn           |
| credit_score     | t-test     |  <0.001 |   d = 0.103 | Negligible | Very small difference                   |
| tenure           | t-test     |  <0.001 |   d = 0.094 | Negligible | Very small difference                   |
| gender           | Chi-square |  <0.001 |   V = 0.058 | Negligible | Very weak association                   |
| balance          | t-test     |   0.885 |   d = 0.001 | None       | No meaningful relationship              |

## Individual Hypotheses

### 1. Tenure vs Churn

* **H₀:** Mean tenure is the same for churned and retained customers.
* **H₁:** Mean tenure differs between churned and retained customers.
* **Test:** Independent samples t-test.
* **Result:** t = −11.745, p < 0.001, d = −0.094.
* **Decision:** Reject H₀.
* **Finding:** Tenure is statistically significant but has a negligible practical effect.
* The effect dropped from d = 0.111 to 0.094 after removing 174 future-dated churn records, all of which were tenure-0 customers (see profiling report, issue #7).

### 2. Credit Score vs Churn

* **H₀:** Mean credit score is the same for churned and retained customers.
* **H₁:** Mean credit score differs between churned and retained customers.
* **Test:** Independent samples t-test.
* **Result:** t = −12.918, p < 0.001, d = −0.103.
* **Decision:** Reject H₀.
* **Finding:** Credit score is statistically significant but has a negligible effect.

### 3. Number of Products vs Churn

* **H₀:** Number of products and churn are independent.
* **H₁:** Number of products and churn are associated.
* **Test:** Chi-square test.
* **Result:** χ² = 7003.316, p < 0.001, V = 0.265.
* **Decision:** Reject H₀.
* **Finding:** Product count has a modest association with churn. Customers with different product counts have substantially different churn rates.

### 4. Geography vs Churn

* **H₀:** Geography and churn are independent.
* **H₁:** Geography and churn are associated.
* **Test:** Chi-square test.
* **Result:** χ² = 1799.123, p < 0.001, V = 0.134.
* **Decision:** Reject H₀.
* **Finding:** Geography has a small overall effect, but the raw churn rates show an important business difference:

  * Germany: **27.96%**
  * France: **15.89%**
* Cramér's V can understate the practical importance of differences in small categorical tables, so the raw churn rates should also be considered.

### 5. Gender vs Churn

* **H₀:** Gender and churn are independent.
* **H₁:** Gender and churn are associated.
* **Test:** Chi-square test.
* **Result:** χ² = 338.537, p < 0.001, V = 0.058.
* **Decision:** Reject H₀.
* **Finding:** Gender is statistically significant but has a negligible practical effect.

### 6. Active Member vs Churn

* **H₀:** Active-member status and churn are independent.
* **H₁:** Active-member status and churn are associated.
* **Test:** Chi-square test.
* **Result:** χ² = 5283.047, p < 0.001, V = 0.230.
* **Decision:** Reject H₀.
* **Finding:** Active-member status has a modest association with churn and indicates the importance of customer engagement.

### 7. Monthly Logins vs Churn

* **H₀:** Mean monthly logins are the same for churned and retained customers.
* **H₁:** Mean monthly logins differ between churned and retained customers.
* **Test:** Independent samples t-test.
* **Result:** t = −66.044, p < 0.001, d = −0.529.
* **Decision:** Reject H₀.
* **Finding:** Monthly login activity has the strongest effect among the tested variables.

### 8. Age vs Churn

* **H₀:** Mean age is the same for churned and retained customers.
* **H₁:** Mean age differs between churned and retained customers.
* **Test:** Independent samples t-test.
* **Result:** t = −26.597, p < 0.001, d = −0.213.
* **Decision:** Reject H₀.
* **Finding:** Age has a small practical association with churn.

### 9. Balance vs Churn

* **H₀:** Mean balance is the same for churned and retained customers.
* **H₁:** Mean balance differs between churned and retained customers.
* **Test:** Independent samples t-test.
* **Result:** t = −0.144, p = 0.885, d = −0.001.
* **Decision:** Fail to reject H₀.
* **Finding:** Balance shows no statistically significant or practically meaningful relationship with churn.

## What We Found

* **Monthly logins, number of products, and active-member status** show the strongest associations with churn.
* **Germany's churn rate is 27.96% compared with 15.89% in France**, making geography an important business finding despite its small Cramér's V.
* Gender, tenure, and credit score are statistically significant but have negligible practical effects.
* Balance shows no meaningful relationship with churn.
* Statistical significance does not necessarily mean business importance, especially with **n = 100,000**.
* These results show **association, not causation**.

## Main Finding

> **Customer engagement variables show the strongest associations with churn, while most demographic and financial variables have small or negligible effects.**

These findings will be used as a starting point for the **predictive modeling phase**.