from Backend.services.market_data_router import (
    MarketDataRouter
)

from Backend.tools.indicators import (
    calculate_rsi,
    calculate_macd
)

router = MarketDataRouter()


def market_agent(state):

    # =====================================
    # GET RESOLVED ASSET
    # =====================================
    resolved_asset = state["resolved_asset"]

    ticker = resolved_asset["ticker"]

    # =====================================
    # GET MARKET DATA
    # =====================================
    df = router.get_price_history(
        ticker=ticker,
        period="1y"
    )

    # =====================================
    # CALCULATE TECHNICAL INDICATORS
    # =====================================
    rsi = calculate_rsi(df)

    macd = calculate_macd(df)

    # =====================================
    # STORE ANALYSIS
    # =====================================
    return {
        "market_analysis": {
            "rsi": rsi,
            "macd": macd
        }
    }