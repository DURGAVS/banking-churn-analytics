CREATE DATABASE bank_analytics;
use bank_analytics;
-- branches.
CREATE TABLE branches (
    branch_id INT,
    branch_name VARCHAR(100),
    city varchar(30),
country varchar(30),
 region varchar(30),
 opened_year int, 
 staff_count int,
    PRIMARY KEY (branch_id)
);

-- products
create TABLE products(
product_id INT, product_name VARCHAR(50), category VARCHAR(40), monthly_fee DECIMAL(6,2), risk_weight DECIMAL(3,2),
PRIMARY KEY(product_id)
);


-- customers
CREATE TABLE customers (
    customer_id INT,
    surname VARCHAR(100),
    geography VARCHAR(30),
    gender VARCHAR(20),
    age INT,
    credit_score INT,
    tenure INT,
    join_date DATE NOT NULL,
    balance DECIMAL(12,2),
    estimated_salary DECIMAL(12,2),
    num_products INT,
    has_cr_card TINYINT,
    is_active_member TINYINT,
    branch_id INT,
    segment VARCHAR(30),
    complaints_last_year INT,
    monthly_logins INT,
    exited TINYINT,
    churn_date DATE,
    age_was_missing TINYINT,
    credit_score_was_missing TINYINT,
    estimated_salary_was_missing TINYINT,
    
    PRIMARY KEY (customer_id),
    INDEX idx_exited (exited),
    INDEX idx_geography (geography),
    INDEX idx_branch (branch_id),
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);
-- customer_products
CREATE TABLE customer_products (
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    opened_date DATE NOT NULL,
    closed_date DATE,
    status VARCHAR(20) NOT NULL,
    PRIMARY KEY (customer_id, product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
-- loans

CREATE TABLE loans (
    loan_id INT,
    customer_id INT NOT NULL,
    loan_type VARCHAR(30),
    loan_amount DECIMAL(12,2),
    interest_rate DECIMAL(5,2),
    term_months INT,
    monthly_payment DECIMAL(12,2),
    debt_to_income DECIMAL(5,3),
    credit_utilization DECIMAL(5,3),
    missed_payments_12m INT,
    loan_status VARCHAR(20),
    default_flag TINYINT,
    disbursed_date DATE,

    PRIMARY KEY (loan_id),
    INDEX idx_default_flag (default_flag),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- monthly_activity
CREATE TABLE monthly_activity (
    customer_id INT NOT NULL,
    activity_month DATE NOT NULL,
    num_transactions INT,
    total_debit DECIMAL(12,2),
    total_credit DECIMAL(12,2),
    avg_balance DECIMAL(12,2),

    PRIMARY KEY (customer_id, activity_month),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

SHOW TABLES;
DESCRIBE customers;
SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'bank_analytics'
  AND REFERENCED_TABLE_NAME IS NOT NULL;