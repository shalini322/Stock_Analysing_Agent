from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    ticker: str
    period: str

    price_data: dict
    financial_data: dict

    # Store multiple headlines or summaries
    recent_news: Annotated[list, operator.add]

    analysis: str
    recommendation: str

    # Messages auto-append across nodes
    messages: Annotated[list, operator.add]
