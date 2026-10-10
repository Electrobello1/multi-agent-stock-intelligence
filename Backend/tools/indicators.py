import pandas as pd


def calculate_rsi(df, period=14):

    delta = df["Close"].diff()

    gain = delta.where(delta > 0, 0)

    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return float(rsi.iloc[-1])

def calculate_macd(df):

    close = df["Close"]

    # Handle DataFrame returned instead of Series
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    print(df)
    print(type(df))
    print(df.head())
    print(df.columns)
    print(type(close))
    print(close.head())
    print("TOTAL ROWS:", len(df))
    print("START:", df.index.min())
    print("END:", df.index.max())

    return {
        "macd": float(macd.iloc[-1]),
        "signal": float(signal.iloc[-1])


    }

