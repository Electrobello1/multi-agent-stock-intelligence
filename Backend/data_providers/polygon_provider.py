from massive import RESTClient

from Backend.data_providers.base import (
    MarketDataProvider
)

from Backend.Resilience.breakers import (
    polygon_market_breaker
)

import pandas as pd
import os

from datetime import datetime, timedelta


class PolygonProvider(
    MarketDataProvider
):

    def __init__(self):

        self.client = RESTClient(
            os.getenv("POLYGON_API_KEY")
        )

    def get_price_history(
        self,
        ticker,
        period="1y"
    ):

        end_date = datetime.now()

        start_date = (
            end_date - timedelta(days=365)
        )

        bars = polygon_market_breaker.call(
            self.client.list_aggs,
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=start_date.strftime(
                "%Y-%m-%d"
            ),
            to=end_date.strftime(
                "%Y-%m-%d"
            )
        )

        rows = []

        for bar in bars:

            rows.append(
                {
                    "Date": pd.to_datetime(
                        bar.timestamp,
                        unit="ms"
                    ),

                    "Open": bar.open,
                    "High": bar.high,
                    "Low": bar.low,
                    "Close": bar.close,
                    "Volume": bar.volume
                }
            )

        df = pd.DataFrame(
            rows
        )

        df = df.set_index(
            "Date"
        )

        df = df.sort_index()

        df = df.dropna()

        return df