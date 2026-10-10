from Backend.data_providers.alpha_vantage_provider import AlphaVantageProvider
from Backend.data_providers.polygon_provider import PolygonProvider
from Backend.data_providers.yahoo_provider import YahooProvider
from Backend.services.data_validator import validate_market_data
from Backend.services.data_window import DataWindow


class MarketDataRouter:

    def __init__(self):

        self.providers = [ YahooProvider(), PolygonProvider(),
            AlphaVantageProvider()
        ]

        # 🔥 enforce 1-year trading window
        self.window = DataWindow(window_size=252)

    def get_price_history(self, ticker, period="1y"):

        errors = []
        valid_datasets = []

        for provider in self.providers:

            try:
                df = provider.get_price_history(ticker, period)

                # STEP 1: validate raw data
                if validate_market_data(df):

                    # STEP 2: apply window BEFORE comparing
                    df = self.window.apply(df)

                    valid_datasets.append(df)

                    print(
                        f"Valid + windowed data from "
                        f"{provider.__class__.__name__} | "
                        f"rows={len(df)}"
                    )

            except Exception as e:
                errors.append(str(e))
                continue

        if not valid_datasets:
            raise Exception(f"All providers failed: {errors}")

        # 🔥 choose most complete dataset AFTER windowing
        best_df = max(valid_datasets, key=len)

        return best_df