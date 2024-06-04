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
    top_suppliers = supplier_data.sort_values(by='Combined Score', ascending=False).head(5)
    return top_suppliers[['supplier_name']].to_dict(orient='records')

@app.post("/recommend-suppliers", response_model=list[SupplierResponse])
def recommend_suppliers(request: SupplierRequest):
    if supplier_data.empty:
        raise HTTPException(status_code=500, detail="Supplier data not loaded")

    filtered_data = supplier_data[
        (supplier_data['Country'] == request.country.lower()) & 
        (supplier_data['Product Name'] == request.product_name.lower())
    ]
    
    if filtered_data.empty:
        raise HTTPException(status_code=404, detail="No suppliers found for the specified country and product name")

    user_input = pd.DataFrame([{
        'Financial Score': request.financial_score,
        'Product Review Score': request.product_review_score,
        'Revenue (Million Dollars)': request.revenue
    }])
    
    max_revenue = filtered_data['Revenue (Million Dollars)'].dropna().max()
    user_input['Normalized Revenue'] = user_input['Revenue (Million Dollars)'] / max_revenue * 100
    user_input['Combined Score'] = user_input['Financial Score'] + user_input['Product Review Score'] + user_input['Normalized Revenue']

    filtered_data['Similarity Score'] = (
        abs(filtered_data['Financial Score'] - user_input['Financial Score'].iloc[0]) +
        abs(filtered_data['Product Review Score'] - user_input['Product Review Score'].iloc[0]) +
        abs(filtered_data['Normalized Revenue'] - user_input['Normalized Revenue'].iloc[0])
    )
    
    recommended_suppliers = filtered_data.sort_values(by='Similarity Score').head(5)
    
    return recommended_suppliers[['supplier_name']].to_dict(orient='records')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
