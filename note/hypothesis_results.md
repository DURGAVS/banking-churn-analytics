# Hypothesis Testing Results

## Method

* **t-test** was used for continuous variables.
* **Chi-square test** was used for categorical variables.
* Both **p-value** and **effect size** were reported because the dataset has **100,000 customers**. A large sample can make very small differences statistically significant, so effect size helps measure practical importance.

## Results

| Variable         | Test       | p-value | Effect Size | Strength   | Key Finding                             |
| ---------------- | ---------- | ------: | ----------: | ---------- | --------------------------------------- |
| monthly_logins   | t-test     |  <0.001 |   d = 0.528 | Medium     | Strongest relationship with churn       |
| num_products     | Chi-square |  <0.001 |   V = 0.266 | Modest     | Product count strongly differs by churn |
| is_active_member | Chi-square |  <0.001 |   V = 0.231 | Modest     | Active members have lower churn         |
| age              | t-test     |  <0.001 |   d = 0.214 | Small      | Some association with churn             |
| geography        | Chi-square |  <0.001 |   V = 0.134 | Small      | Germany has much higher churn           |
| tenure           | t-test     |  <0.001 |   d = 0.111 | Negligible | Very small difference                   |
| credit_score     | t-test     |  <0.001 |   d = 0.104 | Negligible | Very small difference                   |
| gender           | Chi-square |  <0.001 |   V = 0.059 | Negligible | Very weak association                   |
| balance          | t-test     |   0.901 |   d = 0.001 | None       | No meaningful relationship              |

## Individual Hypotheses

### 1. Tenure vs Churn

* **H₀:** Mean tenure is the same for churned and retained customers.
* **H₁:** Mean tenure differs between churned and retained customers.
* **Test:** Independent samples t-test.
* **Result:** t = -13.918, p < 0.001, d = -0.111.
* **Decision:** Reject H₀.
* **Finding:** Tenure is statistically significant but has a negligible practical effect.

### 2. Credit Score vs Churn

* **H₀:** Mean credit score is the same for churned and retained customers.
* **H₁:** Mean credit score differs between churned and retained customers.
* **Test:** Independent samples t-test.
* **Result:** p < 0.001, d = 0.104.
* **Decision:** Reject H₀.
* **Finding:** Credit score is statistically significant but has a negligible effect.

### 3. Number of Products vs Churn

* **H₀:** Number of products and churn are independent.
* **H₁:** Number of products and churn are associated.
* **Test:** Chi-square test.
* **Result:** χ² = 7088.334, p < 0.001, V = 0.266.
* **Decision:** Reject H₀.
* **Finding:** Product count has a modest association with churn. Customers with different product counts have substantially different churn rates.

### 4. Geography vs Churn

* **H₀:** Geography and churn are independent.
* **H₁:** Geography and churn are associated.
* **Test:** Chi-square test.
* **Result:** χ² = 1807.452, p < 0.001, V = 0.134.
* **Decision:** Reject H₀.
* **Finding:** Geography has a small overall effect, but the raw churn rates show an important business difference:

  * Germany: **28.18%**
  * France: **16.05%**
* Cramér's V can understate the practical importance of differences in small categorical tables, so the raw churn rates should also be considered.

### 5. Gender vs Churn

* **H₀:** Gender and churn are independent.
* **H₁:** Gender and churn are associated.
* **Test:** Chi-square test.
* **Result:** χ² = 348.149, p < 0.001, V = 0.059.
* **Decision:** Reject H₀.
* **Finding:** Gender is statistically significant but has a negligible practical effect.

### 6. Active Member vs Churn

* **H₀:** Active-member status and churn are independent.
* **H₁:** Active-member status and churn are associated.
* **Test:** Chi-square test.
* **Result:** χ² = 5317.982, p < 0.001, V = 0.231.
* **Decision:** Reject H₀.
* **Finding:** Active-member status has a modest association with churn and indicates the importance of customer engagement.

### 7. Monthly Logins vs Churn

* **H₀:** Mean monthly logins are the same for churned and retained customers.
* **H₁:** Mean monthly logins differ between churned and retained customers.
* **Test:** Independent samples t-test.
* **Result:** p < 0.001, d = 0.528.
* **Decision:** Reject H₀.
* **Finding:** Monthly login activity has the strongest effect among the tested variables.

### 8. Age vs Churn

* **H₀:** Mean age is the same for churned and retained customers.
* **H₁:** Mean age differs between churned and retained customers.
* **Test:** Independent samples t-test.
* **Result:** p < 0.001, d = 0.214.
* **Decision:** Reject H₀.
* **Finding:** Age has a small practical association with churn.

### 9. Balance vs Churn

* **H₀:** Mean balance is the same for churned and retained customers.
* **H₁:** Mean balance differs between churned and retained customers.
* **Test:** Independent samples t-test.
* **Result:** p = 0.901, d = 0.001.
* **Decision:** Fail to reject H₀.
* **Finding:** Balance shows no statistically significant or practically meaningful relationship with churn.

## What We Found

* **Monthly logins, number of products, and active-member status** show the strongest associations with churn.
* **Germany's churn rate is 28.18% compared with 16.05% in France**, making geography an important business finding despite its small Cramér's V.
* Gender, tenure, and credit score are statistically significant but have negligible practical effects.
* Balance shows no meaningful relationship with churn.
* Statistical significance does not necessarily mean business importance, especially with **n = 100,000**.
* These results show **association, not causation**.

## Main Finding

> **Customer engagement variables show the strongest associations with churn, while most demographic and financial variables have small or negligible effects.**

These findings will be used as a starting point for the **predictive modeling phase**.

"Adding two trend features — the ratio and difference between recent and early transaction volume — raised ROC-AUC from 0.716 to 0.973. Feature engineering delivered far more than algorithm selection: the same random forest that underperformed logistic regression on snapshot features (0.693 vs 0.716) outperformed it substantially once trend was included (0.973 vs 0.933)."