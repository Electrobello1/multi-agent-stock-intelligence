import pandas as pd


class DataWindow:

    def __init__(self, window_size=252):
        self.window_size = window_size

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:

        if df is None or df.empty:
            raise Exception("Empty dataframe cannot be windowed")

        # ensure sorted by date
        df = df.sort_index()

        # enforce numeric safety
        df = df.dropna()

        # 🔥 CORE LOGIC: last N trading days
        if len(df) > self.window_size:
            df = df.tail(self.window_size)

        return df