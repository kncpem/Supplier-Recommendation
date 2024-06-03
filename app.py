import warnings
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import uvicorn

warnings.filterwarnings("ignore")

app = FastAPI()

class SupplierCriteria(BaseModel):
    country: str
    state: str
    financial_score: int
    product_review_score: int
    revenue: int


df=pd.read_excel("us_pensvylina_ss316.xlsx")
df['Revenue (Million Dollars)'] = pd.to_numeric(df['Revenue (Million Dollars)'], errors='coerce')

# Normalize the revenue
max_revenue = df['Revenue (Million Dollars)'].dropna().max()
df['Normalized Revenue'] = df['Revenue (Million Dollars)'] / max_revenue * 100

# Replace NaN values in Normalized Revenue with 0
df['Normalized Revenue'] = df['Normalized Revenue'].fillna(0)

# Calculate Combined Score
df['Combined Score'] = df['Financial Score'] + df['Product Review Score'] + df['Normalized Revenue']

# Sort suppliers by Combined Score in descending order
top_suppliers = df.sort_values(by='Combined Score', ascending=False)

# Normalize the revenue
max_revenue = df['Revenue (Million Dollars)'].dropna().max()
df['Normalized Revenue'] = df['Revenue (Million Dollars)'] / max_revenue * 100

# Replace NaN values in Normalized Revenue with 0
df['Normalized Revenue'] = df['Normalized Revenue'].fillna(0)

def recommend_suppliers(country, state, financial_score, product_review_score, revenue):
    # Filter based on user input
    filtered_df = df[
        (df['Country'] == country) &
        (df['State'] == state) &
        (df['Financial Score'] >= financial_score) &
        (df['Product Review Score'] >= product_review_score) &
        (df['Revenue (Million Dollars)'] >= revenue)
    ]
    
    # Calculate a combined score
    filtered_df['Combined Score'] = (
        filtered_df['Financial Score'] * 0.4 +
        filtered_df['Product Review Score'] * 0.3 +
        filtered_df['Normalized Revenue'] * 0.3
    )
    
    # Sort by the combined score in descending order
    recommended_suppliers = filtered_df.sort_values(by='Combined Score', ascending=False)
    
    return recommended_suppliers

@app.post("/recommend_suppliers/")
def get_top_suppliers(data: SupplierCriteria):
    data = data.dict()
    country = data["country"]
    state = data["state"]
    financial_score = data["financial_score"]
    product_review_score = data["product_review_score"]
    revenue = data["revenue"]
    return recommend_suppliers(country, state, financial_score, product_review_score, revenue)

if __name__ == "__main__":
    uvicorn.run("app:app", host='127.0.0.1', port=8000, reload=True)
