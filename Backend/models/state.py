from typing import TypedDict, Optional, List, Any


class StockState(TypedDict, total=False):

    # -----------------------------------
    # USER INPUT
    # -----------------------------------
    query: str

    # -----------------------------------
    # INTENT
    # -----------------------------------
    intent: Any

    # -----------------------------------
    # RESOLVED ASSET
    # -----------------------------------
    resolved_asset: Optional[dict]

    # -----------------------------------
    # MARKET ANALYSIS
    # -----------------------------------
    market_analysis: Optional[dict]

    # -----------------------------------
    # FUNDAMENTALS
    # -----------------------------------
    fundamentals_analysis: Optional[dict]

    # -----------------------------------
    # NEWS
    # -----------------------------------
    news_analysis: Optional[dict]

    # -----------------------------------
    # SENTIMENT
    # -----------------------------------
    sentiment_analysis: Optional[dict]

    # -----------------------------------
    # RISK
    # -----------------------------------
    risk_analysis: Optional[dict]

    # -----------------------------------
    # STRATEGY
    # -----------------------------------
    strategy_analysis: Optional[dict]

    # -----------------------------------
    # FINAL RECOMMENDATION
    # -----------------------------------
    recommendation: Optional[dict]

    # -----------------------------------
    # LLM INVESTMENT REPORT
    # -----------------------------------
    llm_report: Optional[str]

    # -----------------------------------
    # CONVERSATION MEMORY
    # -----------------------------------
    conversation_history: Optional[List[dict]]

    # -----------------------------------
    # VECTOR / RAG MEMORY
    # -----------------------------------
    retrieved_context: Optional[List[dict]]

    # -----------------------------------
    # CHAT RESPONSE
    # -----------------------------------
    chat_response: Optional[str]

    # -----------------------------------
    # RECOMMENDATION RESPONSE
    # -----------------------------------
    recommendation_response: Optional[str]

    # -----------------------------------
    # USER PROFILE
    # -----------------------------------
    user_profile: Optional[dict]

    # -----------------------------------
    # AUTHENTICATION / SESSION
    # -----------------------------------
    user_id: Any
    session_id: Any

    # -----------------------------------
    # SAVED ANALYSIS
    # -----------------------------------
    analysis_id: Any
    latest_analysis: Optional[dict]

    # -----------------------------------
    # PORTFOLIO
    # -----------------------------------
    portfolio: Optional[dict]

    # -----------------------------------
    # MARKET SUMMARY
    # -----------------------------------
    market_summary: Optional[dict]

    # -----------------------------------
    # RECOMMENDATION WORKFLOW
    # -----------------------------------
    recommendation_candidates: Optional[List[dict[str, Any]]]