import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.db_config import get_engine

engine = get_engine()

branches = pd.read_csv("data/raw/branches.csv")
branches.to_sql(name="branches", con=engine, if_exists="append", index=False)
print("Loaded branches:", len(branches))

products= pd.read_csv("data/raw/products.csv")
products.to_sql(name="products", con=engine, if_exists="append", index=False)
print("Loaded products:", len(products))

customers = pd.read_csv("data/processed/customers_clean.csv")
customers.to_sql(name="customers", con=engine, if_exists="append", index=False)
print("Loaded customers:", len(customers))

customer_products = pd.read_csv("data/raw/customer_products.csv")
customer_products.to_sql(name="customer_products", con=engine, if_exists="append", index=False)
print("Loaded customer_products:", len(customer_products))

loans = pd.read_csv("data/raw/loans.csv")
loans.to_sql(name="loans", con=engine, if_exists="append", index=False)
print("Loaded loans:", len(loans))

monthly_activity = pd.read_csv("data/raw/monthly_activity.csv")
monthly_activity.to_sql(name="monthly_activity", con=engine, if_exists="append", index  =False)
print("Loaded monthly_activity:", len(monthly_activity))