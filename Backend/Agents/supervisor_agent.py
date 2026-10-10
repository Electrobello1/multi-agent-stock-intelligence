from Backend.Agents.market_agent import (
    market_agent
)
from Backend.Agents.llm_agent import LLMAgent
from Backend.Agents.fundamental_agent import (
    fundamentals_agent
)

from Backend.Agents.news_agent import (
    news_agent
)
from Backend.Agents.strategy_agent import (
    strategy_agent
)

def supervisor_agent(state):

    # =====================================
    # MARKET
    # =====================================
    state = market_agent(state)

    # =====================================
    # FUNDAMENTALS
    # =====================================
    state = fundamentals_agent(state)

    # =====================================
    # NEWS
    # =====================================
    state = news_agent(state)

    state = strategy_agent(state)

    state = LLMAgent(state)

    return state