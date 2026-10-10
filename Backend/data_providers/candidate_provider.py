import logging
from typing import Any, Dict, List

import yfinance as yf
from Backend.Resilience.breakers import candidate_breaker


logger = logging.getLogger(__name__)


class CandidateProvider:
    """
    Base interface for discovering investment candidates.
    """

    def get_candidates(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError


class YahooFinanceCandidateProvider(CandidateProvider):
    """
    Discovers stock candidates using Yahoo Finance.

    Candidates are ranked primarily by their
    1-year price performance.
    """

    def get_candidates(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:

        if limit <= 0:
            return []

        try:
            result = candidate_breaker.call(
                yf.screen,
                "day_gainers",
                count=100
            )

            quotes = result.get(
                "quotes",
                []
            )

            candidates: List[Dict[str, Any]] = []

            for quote in quotes:

                ticker = quote.get("symbol")

                if not ticker:
                    continue

                one_year_performance = quote.get(
                    "fiftyTwoWeekChangePercent"
                )

                if one_year_performance is None:
                    continue

                candidate = {
                    "ticker": ticker,
                    "company_name": (
                        quote.get("longName")
                        or quote.get("shortName")
                        or ticker
                    ),
                    "current_price": quote.get(
                        "regularMarketPrice"
                    ),
                    "one_year_performance": (
                        one_year_performance
                    ),
                    "market_cap": quote.get(
                        "marketCap"
                    ),
                    "currency": quote.get(
                        "currency"
                    )
                }

                candidates.append(candidate)

            candidates.sort(
                key=lambda candidate: (
                    candidate["one_year_performance"]
                ),
                reverse=True
            )

            return candidates[:limit]

        except Exception:
            logger.exception(
                "Failed to retrieve stock candidates "
                "from Yahoo Finance."
            )
            raise