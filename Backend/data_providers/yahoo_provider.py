

import yfinance as yf
import pandas as pd
import datetime as dt
from Backend.Resilience.breakers import (
    yahoo_market_breaker
)


class YahooProvider:

    def get_price_history(self, ticker, period="1y"):

        end = dt.datetime.today()
        start = end - dt.timedelta(days=365)

        df = yahoo_market_breaker.call(
            yf.download,
            tickers=ticker,
            start=start,
            end=end,
            interval="1d",
            auto_adjust=True,
            progress=False
        )


        if df is None or df.empty:
            raise Exception("No data returned from Yahoo")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df