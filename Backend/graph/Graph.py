from langgraph.graph import (
    StateGraph,
    START,
    END
)

from Backend.models.state import StockState

from Backend.Agents.asset_agent import (
    asset_resolver_agent
)

from Backend.Agents.market_agent import (
    market_agent
)

from Backend.Agents.fundamental_agent import (
    fundamentals_agent
)

from Backend.Agents.news_agent import (
    news_agent
)

from Backend.Agents.strategy_agent import (
    strategy_agent
)

from Backend.Agents.memory_agent import (
    memory_agent
)

from Backend.Agents.llm_agent import (
    LLMAgent
)

from Backend.Agents.intent_agent import (
    intent_router_node
)

from Backend.Agents.recommendation_agent import (
    recommendation_candidate_agent
)

from Backend.Routing.intent import Intent

from Backend.Agents.conversation_agent import (
    conversation_memory_agent,
    save_chat_response_agent
)


# ======================================
# LLM AGENT
# ======================================

llm_agent = LLMAgent()


# ======================================
# HELPER NODES
# ======================================

def report_llm_node(state):

    return llm_agent.run(
        state,
        Intent.REPORT
    )


def chat_llm_node(state):

    return llm_agent.run(
        state,
        Intent.CHAT
    )


# ======================================
# INTENT ROUTING
# ======================================

def route_intent(state):

    intent = state["intent"]

    if intent == Intent.REPORT:
        return "report"

    if intent == Intent.CHAT:
        return "chat"

    if intent == Intent.RECOMMEND:
        return "recommend"

    raise ValueError(
        f"Unsupported intent: {intent}"
    )


# ======================================
# GRAPH FACTORY
# ======================================

def build_graph(
    intent_node=intent_router_node,
    asset_node=asset_resolver_agent,
    market_node=market_agent,
    fundamentals_node=fundamentals_agent,
    news_node=news_agent,
    strategy_node=strategy_agent,
    memory_node=memory_agent,
    report_node=report_llm_node,
    chat_node=chat_llm_node,
    conversation_memory_node=conversation_memory_agent,
    save_chat_node=save_chat_response_agent,
    recommendation_node=recommendation_candidate_agent,
):

    # ======================================
    # BUILD GRAPH
    # ======================================

    workflow = StateGraph(
        StockState
    )

    # ======================================
    # NODES
    # ======================================

    workflow.add_node(
        "intent_router",
        intent_node
    )

    workflow.add_node(
        "asset_resolver",
        asset_node
    )

    workflow.add_node(
        "market",
        market_node
    )

    workflow.add_node(
        "fundamentals",
        fundamentals_node
    )

    workflow.add_node(
        "news",
        news_node
    )

    workflow.add_node(
        "strategy",
        strategy_node
    )

    workflow.add_node(
        "memory",
        memory_node
    )

    workflow.add_node(
        "llm_report",
        report_node
    )

    workflow.add_node(
        "llm_chat",
        chat_node
    )

    workflow.add_node(
        "conversation_memory",
        conversation_memory_node
    )

    workflow.add_node(
        "save_chat_response",
        save_chat_node
    )

    workflow.add_node(
        "recommendation_candidates",
        recommendation_node
    )

    # ======================================
    # START
    # ======================================

    workflow.add_edge(
        START,
        "intent_router"
    )

    # ======================================
    # INTENT ROUTING
    # ======================================

    workflow.add_conditional_edges(
        "intent_router",
        route_intent,
        {
            "report": "asset_resolver",
            "chat": "conversation_memory",
            "recommend": "recommendation_candidates"
        }
    )

    # ======================================
    # REPORT FAN-OUT
    # ======================================

    workflow.add_edge(
        "asset_resolver",
        "market"
    )

    workflow.add_edge(
        "asset_resolver",
        "fundamentals"
    )

    workflow.add_edge(
        "asset_resolver",
        "news"
    )

    # ======================================
    # REPORT FAN-IN
    #
    # Strategy runs only after ALL THREE:
    # market + fundamentals + news
    # ======================================

    workflow.add_edge(
        [
            "market",
            "fundamentals",
            "news"
        ],
        "strategy"
    )

    # ======================================
    # FINAL REPORT PIPELINE
    # ======================================

    workflow.add_edge(
        "strategy",
        "llm_report"
    )

    workflow.add_edge(
        "llm_report",
        "memory"
    )

    workflow.add_edge(
        "memory",
        END
    )

    # ======================================
    # CHAT FLOW
    # ======================================

    workflow.add_edge(
        "conversation_memory",
        "llm_chat"
    )

    workflow.add_edge(
        "llm_chat",
        "save_chat_response"
    )

    workflow.add_edge(
        "save_chat_response",
        END
    )

    # ======================================
    # RECOMMENDATION FLOW
    # ======================================

    workflow.add_edge(
        "recommendation_candidates",
        END
    )

    # ======================================
    # COMPILE
    # ======================================

    return workflow.compile()


# ======================================
# PRODUCTION GRAPH
# ======================================

graph = build_graph()