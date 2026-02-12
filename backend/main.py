from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import traceback
from graph import create_stock_analysis_graph
from utils.llm import get_llm
from tools.finance import fetch_stock_price, fetch_financial_statements

app = FastAPI(title="Stock Analysis API")

try:
    graph = create_stock_analysis_graph()
    llm = get_llm()
except Exception as e:
    print(f"INITIALIZATION ERROR: {e}")

class AnalysisRequest(BaseModel):
    ticker: str
    period: str

def sanitize_for_json(obj):
    """
    Recursively replaces JSON-incompatible values (NaN, Inf) with None
    and converts Pandas objects to native Python lists/dicts.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (pd.Series, pd.Index)):
        return sanitize_for_json(obj.tolist())
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    return obj

@app.post("/analyze")
async def run_analysis(request: AnalysisRequest):
    clean_ticker = request.ticker.upper().strip()

    # 🔹 FETCH PRICE DATA HERE
    price_data = fetch_stock_price(clean_ticker)

    if "error" in price_data:
        return {
            "ticker": clean_ticker,
            "period": request.period,
            "price_data": price_data,
            "financial_data": {},
            "analysis": "Error: Unable to fetch market data.",
            "recommendation": "Cannot generate recommendation due to missing data.",
            "messages": [f"❌ {price_data['error']}"]
        }

    # 🔹 Initial LangGraph state
    initial_state = {
        "ticker": clean_ticker,
        "period": request.period,
        "price_data": price_data,
        "financial_data": {},
        "analysis": "",
        "recommendation": "",
        "messages": [],
    }

    try:
        print(f"🚀 Starting analysis for: {clean_ticker}")

        result = graph.invoke(initial_state)

        valuation = result.get("valuation", {})
        if valuation:
            mc = valuation.get("market_cap")
            if not price_data.get("market_cap"):
                price_data["market_cap"] = mc

        result["price_data"] = price_data

        safe_result = sanitize_for_json(result)

        print(f"✅ Analysis complete for: {clean_ticker}")
        return safe_result

    except Exception as e:
        print("❌ BACKEND CRASH DETECTED:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Workflow Error: {str(e)}"
        )

@app.post("/chat")
async def chat_with_agent(data: dict):
    try:
        # Safely extract data with defaults
        context = data.get('context', 'No context provided')
        history = data.get('history', 'No history')
        user_input = data.get('prompt', '')
        
        prompt = f"Context:\n{context}\n\nHistory:\n{history}\n\nQuestion: {user_input}"
        response = llm.invoke(prompt)
        
        return {"response": response.content}
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Using reload=True helps during debugging
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
