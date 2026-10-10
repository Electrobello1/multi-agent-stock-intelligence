from Backend.Routing.intent_router import IntentRouter


intent_router = IntentRouter()


def intent_router_node(state):
    """
    Validate the user input and determine the intent.
    """

    query = state.get("query")

    if query is None:
        raise ValueError(
            "A message is required."
        )

    query = query.strip()

    if not query:
        raise ValueError(
            "Message cannot be empty."
        )

    state["query"] = query

    intent = intent_router.route(
        query
    )

    return{"intent" :intent}

