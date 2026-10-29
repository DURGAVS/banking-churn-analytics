# Churn Prediction: Modeling Results

## Goal

Predict which **retained** customers are likely to churn, so the bank can contact them before they leave. The model's output is a churn probability for every customer, a risk level (High / Medium / Low), and a call list ranked by expected loss.

## Features

Features were chosen using the effect sizes from the hypothesis tests, plus two engineered trend features:

| Feature | Why it was included |
| --- | --- |
| `monthly_logins` | Strongest single effect in hypothesis testing (d = 0.529) |
| `num_products` | Modest effect (V = 0.265); churn is lowest at 2 products |
| `is_active_member` | Modest effect (V = 0.230) |
| `age_group` | Small effect (d = 0.213); churn peaks at 45–59 |
| `geography` | Small effect (V = 0.134), but Germany churns at 27.96% vs 15.89% in France |
| `complaints_last_year` | Direct signal of dissatisfaction |
| `tenure` | Negligible on its own (d = 0.094), kept as a control |
| `txn_ratio` | **Engineered:** average transactions in the last 3 months ÷ first 3 months |
| `txn_change` | **Engineered:** last-3-month average minus first-3-month average |

`churn_date` was deliberately excluded. Only churned customers have one, so including it would leak the answer into the model.

## Results

Trained on 80,000 customers and tested on the remaining 20,000 (stratified split, churn rate 19.32% in both).

| Model | ROC-AUC | Churner precision | Churner recall |
| --- | ---: | ---: | ---: |
| Logistic regression (test set) | 0.930 | 0.547 | 0.884 |
| Random forest (test set) | **0.970** | **0.783** | **0.876** |
| Random forest (5-fold out-of-fold, all 100,000 customers) | 0.971 | – | – |

The random forest is the stronger model. It catches almost the same share of churners as logistic regression (87.6% vs 88.4%) while raising far fewer false alarms (precision 0.78 vs 0.55).

The out-of-fold AUC (0.971) is almost identical to the test-set AUC (0.970), which confirms the scores used on the dashboard are consistent with the held-out test.

## Feature engineering mattered more than the algorithm

The two trend features account for **72%** of the random forest's feature importance (`txn_ratio` 0.469 + `txn_change` 0.254). The next most important feature, `monthly_logins`, contributes only 0.071.

In an earlier run without the trend features, ROC-AUC was roughly **0.72** for logistic regression and **0.69** for the random forest. Adding the trend features raised it to **0.93** and **0.97**. The same random forest that underperformed logistic regression on snapshot features outperformed it once trend was included. *(The baseline figures come from a run before the future-churn fix described in the profiling report, issue #7, so they are approximate.)*

**Takeaway:** how a customer's behavior is *changing* predicts churn far better than a snapshot of who they are.

## Threshold choice

The threshold decides how high a churn probability must be before a customer is flagged. Logistic regression on the test set:

| Threshold | Flagged | Churners caught | Precision | Recall |
| ---: | ---: | ---: | ---: | ---: |
| 0.3 | 8,072 | 3,656 | 0.453 | 0.946 |
| 0.5 | 6,236 | 3,414 | 0.547 | 0.884 |
| 0.7 | 4,478 | 2,963 | 0.662 | 0.767 |

**Chosen threshold: 0.3.** A missed churner means a lost customer and their full balance, while a false alarm costs one retention call. Because a missed churner is far more expensive than an unnecessary call, the threshold favours recall: 0.3 catches 94.6% of churners, 242 more than at 0.5, in exchange for about 1,800 extra calls. If the retention team's capacity is limited, 0.5 is the fallback, and the expected-loss ranking (below) ensures the most valuable customers are contacted first either way.

## What the model says (logistic regression coefficients)

Logistic regression is less accurate, but its coefficients are easy to explain to a business audience:

| Feature | Coefficient | Meaning |
| --- | ---: | --- |
| `txn_change` | −1.74 | A drop in transactions strongly predicts churn |
| `is_active_member` | −1.44 | Active members are much less likely to churn |
| `txn_ratio` | −1.09 | Same signal as `txn_change`, measured as a ratio |
| `geography_Germany` | +0.35 | Germany raises churn risk even after controlling for everything else |
| `age_group_45-59` | +0.32 | Middle-aged customers are at higher risk |
| `complaints_last_year` | +0.27 | Each complaint raises risk |

## Scoring and the call list

Every customer is scored in `07_score_customers.py` using **5-fold out-of-fold predictions**: each customer is scored by a model that never saw them during training.

An earlier version scored customers with the same model that had trained on them. Those in-sample scores were overconfident: retained customers the model had already seen were pushed toward zero risk, which **hid** real risk. After switching to out-of-fold scoring, the expected loss of the top 500 customers rose from about €63M to **€83.5M**.

Risk levels for the 80,681 retained customers:

| Risk level | Probability | Customers |
| --- | --- | ---: |
| High | > 0.6 | 3,508 |
| Medium | 0.3 – 0.6 | 4,029 |
| Low | ≤ 0.3 | 73,144 |

These figures come from the latest scoring run, triggered by the weekly automation pipeline. Random-forest scores shift slightly between runs (the top 500 moved from €83.3M to €83.5M), but the risk split and the concentration of risk stay stable.

The call list ranks retained customers by **expected loss** (churn probability × customer value), not probability alone, so the team calls the customers with the most at stake first.

**Key business result:** total value at risk across all retained customers is **€586M**. The top 500 customers carry **€83.5M** of it. That means **0.6% of customers carry 14% of the risk**, so a small retention team focused on 500 people addresses a large share of the exposure.

`customer_value` is defined as balance + 10% of estimated salary. This is a modeling assumption, not a standard banking metric. A real bank would use actual customer lifetime value.

## Limitations

### Synthetic data

The dataset was generated with a built-in relationship between activity decline and churn, applied consistently to all churned customers. The ROC-AUC of 0.97 reflects that design. Real banking data would show a noisier relationship and lower model performance. The methodology transfers; the score does not.

### Feature timing

The trend features use the full 12-month activity window, including months after some customers had already churned. In production, features must come from an observation window that ends **before** the prediction window, otherwise the model sees the outcome it is trying to predict.

### Active loans may default later

The loans table currently records 3,464 loans as Default, while 20,322 loans are still Active. Some of these active loans may default in the future, so the observed 11.8% default rate should be treated as a floor rather than a final default rate.

### Median imputation compressed credit score variance

There were 2,100 missing credit scores, which were replaced with the median value. This reduced the standard deviation from 95.36 to 94.33, meaning the imputation slightly compressed the observed variation in credit scores and may affect analyses that depend on their distribution.

### Customers with under 12 months of history cannot be scored reliably

The trend features compare a customer's first three months with their last three months within a 12-month activity window. Customers with less than 12 months of history do not have enough data to calculate these trend features reliably.
