from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd

app = FastAPI()

class SupplierRequest(BaseModel):
    country: str
    financial_score: float
    product_review_score: float
    revenue: float
    product_name: str

class SupplierResponse(BaseModel):
    supplier_name: str

# Load and preprocess the data
def load_and_preprocess_data(file_path: str):
    df = pd.read_excel(file_path)
    df['Revenue (Million Dollars)'] = pd.to_numeric(df['Revenue (Million Dollars)'], errors='coerce')

    max_revenue = df['Revenue (Million Dollars)'].dropna().max()
    df['Normalized Revenue'] = df['Revenue (Million Dollars)'] / max_revenue * 100
    df['Normalized Revenue'] = df['Normalized Revenue'].fillna(0)
    df['Combined Score'] = df['Financial Score'] + df['Product Review Score'] + df['Normalized Revenue']
    df = df.rename(columns={'Supplier Name': 'supplier_name'})
    df['Country'] = df['Country'].str.lower()
    df['Product Name'] = df['Product Name'].str.lower()
    
    return df

# Preload the data
file_path = "us_ss316_Suppliers.xlsx"
supplier_data = load_and_preprocess_data(file_path)

@app.get("/ss316-suppliers", response_model=list[SupplierResponse])
def get_top_suppliers():
    if supplier_data.empty:
        raise HTTPException(status_code=500, detail="Supplier data not loaded")
    top_suppliers = supplier_data.sort_values(by='Combined Score', ascending=False).head(4)
    return top_suppliers[['supplier_name']].to_dict(orient='records')

@app.post("/recommend-suppliers", response_model=list[SupplierResponse])
def recommend_suppliers(request: SupplierRequest):
    if supplier_data.empty:
        raise HTTPException(status_code=500, detail="Supplier data not loaded")

    # Step 1: Filter based on country and product name
    filtered_data = supplier_data[
        (supplier_data['Country'] == request.country.lower()) & 
        (supplier_data['Product Name'] == request.product_name.lower())
    ]
    
    if filtered_data.empty:
        raise HTTPException(status_code=404, detail="No suppliers found for the specified country and product name")

    # Step 2: Further filter based on financial score, product review score, and revenue
    filtered_data = filtered_data[
        (filtered_data['Financial Score'] > request.financial_score) &
        (filtered_data['Product Review Score'] > request.product_review_score) &
        (filtered_data['Revenue (Million Dollars)'] > request.revenue)
    ]
    
    if filtered_data.empty:
        raise HTTPException(status_code=404, detail="No suppliers match the provided criteria")

    # Step 3: Calculate the combined score and recommend top suppliers
    max_revenue = filtered_data['Revenue (Million Dollars)'].dropna().max()
    filtered_data['Normalized Revenue'] = filtered_data['Revenue (Million Dollars)'] / max_revenue * 100
    filtered_data['Combined Score'] = filtered_data['Financial Score'] + filtered_data['Product Review Score'] + filtered_data['Normalized Revenue']

    recommended_suppliers = filtered_data.sort_values(by='Combined Score', ascending=False).head(4)
    
    return recommended_suppliers[['supplier_name']].to_dict(orient='records')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
