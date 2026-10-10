
def validate_market_data(df):

    if df is None or df.empty:
        return False

    required = ["Open", "High", "Low", "Close", "Volume"]

    if not all(col in df.columns for col in required):
        return False

    # allow raw data, window will handle size
    if len(df) < 30:
        return False

    return True