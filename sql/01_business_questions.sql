#Churn rate by geography:
SELECT geography,
COUNT(*) AS CUSTOMERS,
SUM(Exited) AS CHURNED,
round(AVG(Exited)*100,2) AS CHURN_RATE
from customers
group by geography
order by CHURN_RATE DESC;

-- Churn rate by gender
SELECT gender,
count(*) as CUSTOMERS,
SUM(exited) as CHURNED,
ROUND(AVG(exited)*100,2) as churn_rate
from customers
group by gender
order by churn_rate desc;

-- churn by age bucket

select
case
when age<30 then 'under 30'
when age<45 then '30-44'
when age<60 then '45-59'
else '60+'
end as age_group,
count(*) as customers,
sum(exited) as churned,
round(avg(exited)*100,2) as churn_rate_pct
from customers
group by age_group
order by age_group;


-- Churn rate by number of products

select num_products,count(*) as customers,
sum(exited) as churned,
round(avg(exited)*100,2) as churn_rate_pct
from customers
group by num_products
order by num_products;

-- Churn: active vs inactive members

select is_active_member,count(*) as customers,
sum(exited) as churned,
round(avg(exited)*100,2) as churn_rate_pct
from customers
group by is_active_member
order by is_active_member;

-- churn rate per product
select*from customers;
select*from customer_products;
select*from products;

select P.product_name,P.category,
count(*) as Holders,
round(avg(C.exited)*100,2) as churn_rate_pct
from customers C
join customer_products CP
on C.customer_id=CP.customer_id
join products P
on CP.product_id=P.product_id
group by P.product_name,P.category
order by churn_rate_pct desc
;

show tables;
-- Top 10 branches by churn rate	


select B.branch_name,B.city,B.country,count(*) as customers,
round(avg(exited)*100,2) as churn_rate_pct
from customers C
join branches B
on C.branch_id=B.branch_id
group by B.branch_name,B.city,B.country
having customers >=100
order by churn_rate_pct desc
limit 10;


-- Default rate by credit score band	
select
CASE
    WHEN c.credit_score < 580 THEN 'Poor (<580)'
    WHEN c.credit_score < 670 THEN 'Fair (580-669)'
    WHEN c.credit_score < 740 THEN 'Good (670-739)'
    WHEN c.credit_score < 800 THEN 'Very Good (740-799)'
    ELSE 'Excellent (800+)'
END AS score_band,
count(*) as loans,
sum(L.default_flag) as defaults,
round(avg(L.default_flag)*100,2) as default_rate_pct
from customers c
join loans L
on c.customer_id=L.customer_id
group by score_band
ORDER BY AVG(c.credit_score);

-- Avg balance by segment, ranked within country	geography, segment, avg_balance, rank_in_country

with seg as(
select geography,segment,
avg(balance) as avg_balance from customers
group by geography,segment
)
select geography,segment,round(avg_balance,0) as avg_balance,
rank() over(partition by geography order by avg_balance desc) as rank_in_country
from seg;

-- Monthly churn trend	(churn_month, churned_count	DATE_FORMAT, WHERE exited=1

select date_format(churn_date,'%Y-%m') as churn_month,
count(exited) as churned_count
from customers
where exited=1
group by churn_month
order by churn_month;


-- Running total of churned customers	churn_month, monthly_churn, running_total
 with churn as (
 select date_format(churn_date,'%Y-%m') as churn_month,
 count(exited) as monthly_churn
 from customers
 where exited=1
 group by churn_month
 order by churn_month
 )
 select churn_month,monthly_churn,sum(monthly_churn) over(order by churn_month) as running_churn
 from churn
 ;
 
-- month-over-month balance change per customer.
select*from monthly_activity;
select customer_id,activity_month,avg_balance,
LAG(avg_balance) over(partition by customer_id order by activity_month) as prev_balance,
avg_balance-LAG(avg_balance) over(partition by customer_id order by activity_month) as change_
from monthly_activity;




-- Q13: Activity decline as an early-warning signal
--
-- Threshold sweep — precision vs coverage:
--   any decline : 74,187 flagged, 20.49% churn (1.05x baseline)
--   40%+ drop   : 11,421 flagged, 47.40% churn (2.43x baseline)   <-- recommended
--   50%+ drop   :  3,386 flagged, 56.82% churn (2.91x baseline)
--
-- Baseline churn: 19.5%
-- Recommendation: 40% threshold. Flags 11% of customers and captures
-- 28% of all churners at 2.4x lift.


WITH t AS (
    SELECT customer_id, activity_month, num_transactions,
           LAG(num_transactions, 1) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_1,
           LAG(num_transactions, 2) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_2
    FROM monthly_activity
)
SELECT * FROM t
where prev_2 > prev_1 and prev_1 > num_transactions;


-- . How many distinct customers?
WITH t AS (
    SELECT customer_id, activity_month, num_transactions,
           LAG(num_transactions, 1) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_1,
           LAG(num_transactions, 2) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_2
    FROM monthly_activity
)
SELECT COUNT(DISTINCT customer_id) FROM t WHERE prev_2 > prev_1 and prev_1 > num_transactions;


WITH t AS (
    SELECT customer_id, activity_month, num_transactions,
           LAG(num_transactions, 1) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_1,
           LAG(num_transactions, 2) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_2
    FROM monthly_activity
),
declining AS (
    SELECT DISTINCT customer_id FROM t
    WHERE prev_2 > prev_1 AND prev_1 > num_transactions
)
SELECT
    CASE WHEN d.customer_id IS NULL THEN 'No decline' ELSE 'Declining' END AS grp,
    COUNT(*) AS customers,
    ROUND(AVG(c.exited) * 100, 2) AS churn_rate_pct
FROM customers c
LEFT JOIN declining d ON c.customer_id = d.customer_id
GROUP BY grp;


WITH t AS (
    SELECT customer_id, activity_month, num_transactions,
           LAG(num_transactions, 1) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_1,
           LAG(num_transactions, 2) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_2
    FROM monthly_activity
),
declining AS (
    SELECT DISTINCT customer_id FROM t
   WHERE prev_1 < prev_2 * 0.8
  AND num_transactions < prev_1 * 0.8
)
SELECT
    CASE WHEN d.customer_id IS NULL THEN 'No decline' ELSE 'Declining' END AS grp,
    COUNT(*) AS customers,
    ROUND(AVG(c.exited) * 100, 2) AS churn_rate_pct
FROM customers c
LEFT JOIN declining d ON c.customer_id = d.customer_id

GROUP BY grp;


WITH t AS (
    SELECT customer_id, activity_month, num_transactions,
           LAG(num_transactions, 1) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_1,
           LAG(num_transactions, 2) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_2
    FROM monthly_activity
),
declining AS (
    SELECT DISTINCT customer_id FROM t
   WHERE prev_1 < prev_2 * 0.6
  AND num_transactions < prev_1 * 0.6
)
SELECT
    CASE WHEN d.customer_id IS NULL THEN 'No decline' ELSE 'Declining' END AS grp,
    COUNT(*) AS customers,
    ROUND(AVG(c.exited) * 100, 2) AS churn_rate_pct
FROM customers c
LEFT JOIN declining d ON c.customer_id = d.customer_id

GROUP BY grp;

-- d: each month 50%+ below previous
--      → 3,386 flagged, 56.82% churn — highest precision, low coverage
WITH t AS (
    SELECT customer_id, activity_month, num_transactions,
           LAG(num_transactions, 1) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_1,
           LAG(num_transactions, 2) OVER (PARTITION BY customer_id ORDER BY activity_month) AS prev_2
    FROM monthly_activity
),
declining AS (
    SELECT DISTINCT customer_id FROM t
   WHERE prev_1 < prev_2 * 0.5
  AND num_transactions < prev_1 * 0.5
)
SELECT
    CASE WHEN d.customer_id IS NULL THEN 'No decline' ELSE 'Declining' END AS grp,
    COUNT(*) AS customers,
    ROUND(AVG(c.exited) * 100, 2) AS churn_rate_pct
FROM customers c
LEFT JOIN declining d ON c.customer_id = d.customer_id

GROUP BY grp;





    