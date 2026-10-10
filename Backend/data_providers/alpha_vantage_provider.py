from dotenv import load_dotenv

from alpha_vantage.timeseries import TimeSeries

from Backend.data_providers.base import (
    MarketDataProvider
)

from Backend.Resilience.breakers import (
    alphavantage_market_breaker
)

import os
import pandas as pd


load_dotenv()


class AlphaVantageProvider(MarketDataProvider):

    def __init__(self):

        self.api_key = os.getenv(
            "ALPHA_VANTAGE_API_KEY"
        )

        if not self.api_key:
            raise Exception(
                "Missing ALPHA_VANTAGE_API_KEY in environment"
            )

        self.ts = TimeSeries(
            key=self.api_key,
            output_format="pandas"
        )

    def get_price_history(
        self,
        ticker,
        period="1y"
    ):

        data, meta = alphavantage_market_breaker.call(
            self.ts.get_daily,
            symbol=ticker,
            outputsize="compact"
        )

        if data is None or data.empty:

            raise Exception(
                "Alpha Vantage returned empty dataset"
            )

        data = data.rename(
            columns={
                "1. open": "Open",
                "2. high": "High",
                "3. low": "Low",
                "4. close": "Close",
                "5. volume": "Volume"
            }
        )

        for col in [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]:
            data[col] = pd.to_numeric(
                data[col],
                errors="coerce"
            )

        data = data.sort_index()

        return data