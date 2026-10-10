from Backend.data_providers.fundamentals.fundamental_provider import (
    FundamentalsProvider
)

provider = FundamentalsProvider()


def fundamentals_agent(state):

    # =====================================
    # GET RESOLVED ASSET
    # =====================================
    resolved_asset = state["resolved_asset"]

    ticker = resolved_asset["ticker"]

    # =====================================
    # FETCH FUNDAMENTALS
    # =====================================
    fundamentals = provider.get_fundamentals(
        ticker
    )

    # =====================================
    # UPDATE SHARED STATE
    # =====================================
    return{"fundamentals_analysis":fundamentals}

