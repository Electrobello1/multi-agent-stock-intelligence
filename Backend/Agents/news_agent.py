
from Backend.data_providers.news_provider import (
    MassiveNewsProvider
)




provider = MassiveNewsProvider()


def news_agent(state):

    # =====================================
    # QUERY
    # =====================================
    query = state["query"]

    # =====================================
    # RESOLVE ASSET
    # =====================================
    resolved_asset = state["resolved_asset"]

    ticker = resolved_asset["ticker"]

    # =====================================
    # FETCH NEWS
    # =====================================
    news = provider.get_news(
        ticker=ticker
    )

    # =====================================
    # STORE IN STATE
    # =====================================
    return{"news_analysis":news}

