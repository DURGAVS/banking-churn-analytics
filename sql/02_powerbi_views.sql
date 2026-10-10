-- Views that feed the Power BI dashboard.
-- Business logic (age groups, score bands) lives here in SQL,
-- so Power BI stays simple and any table reload updates the dashboard automatically.
-- Run AFTER 06_model.py has created the churn_scores table.

USE bank_analytics;

-- One row per customer: profile + branch + churn score
CREATE OR REPLACE VIEW vw_customers AS
SELECT
    c.customer_id,
    c.geography,
    c.gender,
    c.age,
    CASE
        WHEN c.age < 30 THEN 'Under 30'
        WHEN c.age < 45 THEN '30-44'
        WHEN c.age < 60 THEN '45-59'
        ELSE '60+'
    END AS age_group,
    c.credit_score,
    CASE
        WHEN c.credit_score < 580 THEN 'Poor (<580)'
        WHEN c.credit_score < 670 THEN 'Fair (580-669)'
        WHEN c.credit_score < 740 THEN 'Good (670-739)'
        WHEN c.credit_score < 800 THEN 'Very Good (740-799)'
        ELSE 'Excellent (800+)'
    END AS score_band,
    c.tenure,
    c.join_date,
    c.balance,
    c.estimated_salary,
    c.num_products,
    c.has_cr_card,
    c.is_active_member,
    c.segment,
    c.complaints_last_year,
    c.monthly_logins,
    c.exited,
    c.churn_date,
    b.branch_name,
    b.city,
    b.region,
    s.churn_probability,
    s.risk_level,
    s.customer_value,
    s.expected_loss,
    CASE WHEN d.customer_id IS NULL THEN 'Stable'
         ELSE 'Sharp decline' END AS activity_trend 
FROM customers c
JOIN branches b      ON c.branch_id = b.branch_id
LEFT JOIN churn_scores s ON c.customer_id = s.customer_id
LEFT JOIN declining_customers d ON c.customer_id = d.customer_id;


-- One row per loan: loan details + borrower profile
CREATE OR REPLACE VIEW vw_loans AS
SELECT
    l.loan_id,
    l.customer_id,
    l.loan_type,
    l.loan_amount,
    l.interest_rate,
    l.term_months,
    l.debt_to_income,
    l.missed_payments_12m,
    l.loan_status,
    l.default_flag,
    l.disbursed_date,
    c.geography,
    c.age,
    c.credit_score,
    CASE
        WHEN c.credit_score < 580 THEN 'Poor (<580)'
        WHEN c.credit_score < 670 THEN 'Fair (580-669)'
        WHEN c.credit_score < 740 THEN 'Good (670-739)'
        WHEN c.credit_score < 800 THEN 'Very Good (740-799)'
        ELSE 'Excellent (800+)'
    END AS score_band
FROM loans l
JOIN customers c ON l.customer_id = c.customer_id;


-- Sanity checks: row counts should match the base tables
SELECT COUNT(*) AS customers_in_view FROM vw_customers;       -- expect 100,000
SELECT COUNT(*) AS scored FROM vw_customers WHERE churn_probability IS NOT NULL;
SELECT COUNT(*) AS loans_in_view FROM vw_loans;               -- expect 29,466

CREATE TABLE declining_customers AS
SELECT customer_id FROM vw_declining;

ALTER TABLE declining_customers ADD PRIMARY KEY (customer_id);

SELECT COUNT(*) FROM declining_customers;   -- should be 3,386

SELECT activity_trend,
       COUNT(*) AS customers,
       ROUND(AVG(exited) * 100, 2) AS churn_rate_pct
FROM vw_customers
GROUP BY activity_trend;