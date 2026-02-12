import requests
import os
from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"

# Shared session with headers
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# =========================================================
# 📈 STOCK PRICE (REALTIME QUOTE)
# =========================================================
def fetch_stock_price(ticker: str) -> dict:
    try:
        ticker = ticker.upper().strip()
        url = f"{BASE_URL}/quote"
        params = {"symbol": ticker, "token": FINNHUB_API_KEY}

        res = session.get(url, params=params, timeout=10)
        data = res.json()

        if not data or data.get("c", 0) == 0:
            return {"ticker": ticker, "error": "Finnhub returned no price data"}

        # Adding 52-week avg placeholder for Streamlit
        fifty_two_week_avg = (data.get("h", 0) + data.get("l", 0)) / 2

        return {
            "ticker": ticker,
            "company_name": ticker,           # Finnhub doesn’t provide company name here
            "current_price": data["c"],
            "open": data["o"],
            "high": data["h"],
            "low": data["l"],
            "previous_close": data["pc"],
            "fifty_two_week_avg": fifty_two_week_avg,
            "market_cap": None,               # Placeholder (will come from financial metrics)
            "price_history": {},              # Optional: could add daily OHLC later
            "source": "finnhub"
        }

    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


# =========================================================
# 🧾 HELPER
# =========================================================
def get_recent_data(items: list, keys: list):
    if not items:
        return {}
    latest = items[0]
    return {key: latest.get(key) for key in keys}


# =========================================================
# 📊 FINANCIAL STATEMENTS / METRICS
# =========================================================
def fetch_financial_statements(ticker: str, period: str = "yearly") -> dict:
    try:
        ticker = ticker.upper().strip()
        url = f"{BASE_URL}/stock/metric"
        params = {"symbol": ticker, "metric": "all", "token": FINNHUB_API_KEY}

        res = session.get(url, params=params, timeout=10).json()
        metrics = res.get("metric", {})

        if not metrics:
            return {"error": "No financial metrics available"}

        # ----- better market_cap handling -----
        market_cap = metrics.get("marketCapitalization")

        # Fallback: price * shares outstanding if market_cap is missing or zero
        if not market_cap:
            current_price = metrics.get("close") or metrics.get("adjClose")
            shares_out = metrics.get("shareOutstanding")
            if current_price and shares_out:
                market_cap = current_price * shares_out

        # -------- main metrics block (for existing UI) --------
        data = {
            "valuation": {
                "market_cap": market_cap,
                "enterprise_value": metrics.get("enterpriseValue"),
                "pe_ratio": metrics.get("peBasicExclExtraTTM") or metrics.get("peTTM"),
                "forward_pe": metrics.get("forwardPE"),
                "ps_ratio": metrics.get("psTTM"),
            },
            "profitability": {
                "eps": metrics.get("epsTTM"),
                "gross_margin": metrics.get("grossMarginTTM"),
                "net_margin": metrics.get("netProfitMarginTTM"),
            },
            "liquidity": {
                "current_ratio": metrics.get("currentRatio"),
                # Finnhub uses totalDebtToEquity, not "totalDebt/totalEquity"
                "debt_to_equity": metrics.get("totalDebtToEquity"),
            },
            "period": period,
            "source": "finnhub",
        }

        # -------- financial_data for tab2 (keys only, values dynamic) --------
        data["financial_data"] = {
            "balance_sheet": {
                "Total Assets": metrics.get("totalAssets"),
                "Total Liabilities": metrics.get("totalLiabilities"),
                "Total Equity": metrics.get("totalEquity"),
                "Cash & Cash Equivalents": metrics.get("cashAndCashEquivalents"),
                "Short-Term Debt": metrics.get("shortTermDebt"),
                "Currency": metrics.get("currency"),
                "Frequency": period,
            },
            "income_statement": {
                "Revenue": metrics.get("revenueTTM"),
                "Cost of Revenue": metrics.get("costOfRevenueTTM"),
                "Gross Profit": metrics.get("grossProfitTTM"),  # better than margin here
                "Operating Expenses": metrics.get("operatingExpenseTTM"),
                "Net Income": metrics.get("netIncomeTTM"),
                "Currency": metrics.get("currency"),
                "Frequency": period,
            },
            "cash_flow": {
                "Operating Cash Flow": metrics.get("operatingCashFlowTTM"),
                "Investing Cash Flow": metrics.get("cashFlowFromInvestingTTM"),
                "Financing Cash Flow": metrics.get("cashFlowFromFinancingTTM"),
                "Net Change in Cash": metrics.get("netCashFlowTTM"),
                "Currency": metrics.get("currency"),
                "Frequency": period,
            },
        }

        return data

    except Exception as e:
        return {"error": str(e)}
