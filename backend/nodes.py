import json
from state import AgentState
from tools.finance import fetch_stock_price, fetch_financial_statements
from utils.llm import get_llm

llm = get_llm()

def fetch_data_node(state: AgentState) -> AgentState:
    ticker, period = state["ticker"], state["period"]

    state.setdefault("messages", [])

    price_data = fetch_stock_price(ticker)
    financial_data = fetch_financial_statements(ticker, period)

    # Detect Alpha Vantage failure / rate limit
    if not price_data or "Note" in price_data or "Error Message" in price_data:
        state["price_data"] = {"error": "Rate limited or invalid ticker"}
        state["financial_data"] = {}
        state["messages"].append(f"❌ Failed to fetch data for {ticker}")
        return state

    state["price_data"] = price_data
    state["financial_data"] = financial_data
    state["messages"].append(f"✓ Fetched data for {ticker}")

    return state

def analyze_financials_node(state: AgentState) -> AgentState:
    price_data = state.get("price_data", {})
    financial_data = state.get("financial_data", {})

    # Hard stop if fetch failed
    if "error" in price_data:
        state["analysis"] = "Error: Unable to fetch market data."
        state["messages"].append("❌ Financial analysis failed")
        return state

    # Summarize price info 
    price_summary = {
        "current_price": price_data.get("current_price"),
        "previous_close": price_data.get("previous_close"),
        "day_high": price_data.get("day_high"),
        "day_low": price_data.get("day_low"),
        "market_cap": price_data.get("market_cap"),
        "pe_ratio": price_data.get("pe_ratio"),
        "50_dma": price_data.get("fifty_day_avg"),
        "200_dma": price_data.get("two_hundred_day_avg"),
    }

    prompt = f"""
Analyze {state['ticker']} stock.

### Market Snapshot
{json.dumps(price_summary, indent=2)}

### Financial Statements
{json.dumps(financial_data, indent=2)}

Provide:
1. Financial Health
2. Valuation Insight
3. Trend Analysis
4. Risk Assessment

Respond in clean Markdown.
"""

    response = llm.invoke(prompt)

    state["analysis"] = response.content
    state["messages"].append("✓ Completed financial analysis")

    return state

def generate_recommendation_node(state: AgentState) -> AgentState:
    analysis = state.get("analysis", "")

    if not analysis or "Error" in analysis:
        state["recommendation"] = "Cannot generate recommendation due to missing or failed analysis."
        return state

    prompt = f"""
Based on the following analysis:

{analysis}

Generate:
- Verdict (Buy / Hold / Sell)
- Confidence Rating out of 5(1–5)
- Risk Level
- Investment Rationale
- Suggested Strategy
and give line gaps after each point. Make it concise and actionable for an investor. Also visually appealing. Use bold for the verdict and confidence rating. and for sentences give a line gap after rating or verdict. also write in points. a bit descriptive but concise. use bold and bigger font for subheading.
"""

    response = llm.invoke(prompt)
    state["recommendation"] = response.content
    state["messages"].append("✓ Generated recommendation")

    return state
