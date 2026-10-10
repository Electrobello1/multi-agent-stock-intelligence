import re

from Backend.tools.asset_lookup import (
    ProductionTickerResolver
)


resolver = ProductionTickerResolver()


# Common company aliases
ASSET_ALIASES = {
    "google": "GOOGL",
    "alphabet": "GOOGL",
}


def normalize_asset_query(query: str) -> str:
    """
    Extract a simple company name or ticker
    from a stock-analysis request.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError(
            "Asset query cannot be empty."
        )

    query = query.strip()

    # Remove common instruction prefixes
    query = re.sub(
        r"^(?:please\s+)?"
        r"(?:analyse|analyze|review|evaluate|assess|"
        r"analysis of|tell me about)\s+",
        "",
        query,
        flags=re.IGNORECASE
    )

    # Remove common stock-related suffixes
    query = re.sub(
        r"\s+(?:stock|shares)$",
        "",
        query,
        flags=re.IGNORECASE
    )

    query = query.strip(" .?!")

    if not query:
        raise ValueError(
            "No company name or ticker was provided."
        )

    # Resolve common aliases
    return ASSET_ALIASES.get(
        query.lower(),
        query
    )


def asset_resolver_agent(state):

    # Original user request
    query = state["query"]

    # Extract company or ticker
    asset_query = normalize_asset_query(
        query
    )

    # Resolve against the asset provider/database
    resolved = resolver.resolve(
        asset_query
    )

    if not resolved:
        raise ValueError(
            f"Could not resolve asset: {asset_query}"
        )

    # Return only this node's update
    return {
        "resolved_asset": resolved
    }