from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import fetch_data_node, analyze_financials_node, generate_recommendation_node

def create_stock_analysis_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node('fetch_data', fetch_data_node)
    workflow.add_node('analyze_financials', analyze_financials_node)
    workflow.add_node('generate_recommendation', generate_recommendation_node)

    workflow.set_entry_point('fetch_data')
    workflow.add_edge('fetch_data', 'analyze_financials')
    workflow.add_edge('analyze_financials', 'generate_recommendation')
    workflow.add_edge('generate_recommendation', END)

    graph = workflow.compile()

    print(graph.get_graph().print_ascii())

    return graph
