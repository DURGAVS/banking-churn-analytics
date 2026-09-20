### Synthetic data
The dataset was generated with a built-in relationship between activity decline and churn, applied consistently to all churned customers. The ROC-AUC of 0.973 reflects that design. Real banking data would show a noisier relationship and lower model performance. The methodology transfers; the score does not.


### Active loans may default later

The loans table currently records 3,464 loans as Default, while 20,322 loans are still Active. Some of these active loans may default in the future, so the observed 11.8% default rate should be treated as a floor rather than a final default rate.

### Median imputation compressed credit score variance

There were 2,100 missing credit scores, which were replaced with the median value. This reduced the standard deviation from 95.36 to 94.33, meaning the imputation slightly compressed the observed variation in credit scores and may affect analyses that depend on their distribution.

### Customers with under 12 months of history cannot be scored

The trend features compare a customer's first three months with their last three months within a 12-month activity window. Customers with less than 12 months of history do not have enough data to calculate these trend features, so they cannot receive a model score using this approach.
