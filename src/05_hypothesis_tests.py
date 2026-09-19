import pandas as pd
from scipy import stats
df=pd.read_csv("data/processed/customers_clean.csv")

# ============================================================
# H2: Do churned customers have lower credit scores?
# H0: mean credit score is the same for churned and retained
# H1: mean credit score differs between the two groups
# ============================================================
churned = df[df['exited'] == 1]['credit_score']
retained = df[df['exited'] == 0]['credit_score']

print("mean credit score - churned:",round(churned.mean(),2))
print("mean credit score - retained:",round(retained.mean(),2))
t_stat, p_value=stats.ttest_ind(churned,retained)
print("T_statistic:",round(t_stat,3))
print("p_value:",p_value)

#"Credit score differs significantly between churned and retained customers (p < 0.001), 
# but the effect is negligible (d = -0.10). The 9.8-point gap is statistically detectable
#  only because of the large sample; it has no practical value for identifying at-risk customers."
import numpy as np
n1, n2 = len(churned), len(retained)
pooled_std = np.sqrt(((n1-1)*churned.std()**2 + (n2-1)*retained.std()**2) / (n1+n2-2))
cohens_d = (churned.mean() - retained.mean()) / pooled_std
print("Cohen's d:", round(cohens_d, 3))


def run_ttest(column):
    churned = df[df["exited"] == 1][column]
    retained = df[df["exited"] == 0][column]
    t_stat, p_value = stats.ttest_ind(churned, retained)
    n1, n2 = len(churned), len(retained)
    pooled_std = np.sqrt(((n1-1)*churned.std()**2 + (n2-1)*retained.std()**2) / (n1+n2-2))
    cohens_d = (churned.mean() - retained.mean()) / pooled_std
    print("Mean", column, "- churned:", round(churned.mean(), 2))
    print("Mean", column, "- retained:", round(retained.mean(), 2))
    print("T_statistic:", round(t_stat, 3))
    print("p_value:", p_value)
    print("cohens_d:", round(cohens_d, 3))
    print()
run_ttest("credit_score")
run_ttest("tenure")
run_ttest("age")
run_ttest("balance")
run_ttest("monthly_logins")

# ============================================================
# RESULTS — t-tests (continuous variables)
#
# column           churned   retained   p-value    Cohen's d
# monthly_logins      4.78       7.38   ~0           -0.528  medium
# age                53.29      56.03   <0.001       -0.214  small
# tenure              4.73       5.08   <0.001       -0.111  negligible
# credit_score      641.26     651.02   <0.001       -0.104  negligible
# balance         76917.42   76986.57    0.901       -0.001  none
#
# Four of five are statistically significant but only monthly_logins
# reaches a meaningful effect size. The others are detectable only
# because n = 100,000. Balance shows no difference at all.
# ============================================================

def run_chi2_test(column):
    contingency_table = pd.crosstab(df[column], df["exited"])
    chi2_stat, p_value, dof, expected = stats.chi2_contingency(contingency_table)
    n = contingency_table.values.sum()
    min_dim = min(contingency_table.shape) - 1
    cramers_v = np.sqrt(chi2_stat / (n * min_dim))
    print("Chi-squared statistic for", column, ":", round(chi2_stat, 3))
    print("p_value:", p_value)
    print("Cramér's V:", round(cramers_v, 3))
    print()

run_chi2_test("geography")
run_chi2_test("gender")
run_chi2_test("num_products")
run_chi2_test("is_active_member")