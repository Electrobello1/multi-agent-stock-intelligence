def strategy_agent(state):

    market = state.get(
        "market_analysis",
        {}
    )

    fundamentals = state.get(
        "fundamentals_analysis",
        {}
    )

    news = state.get(
        "news_analysis",
        []
    )

    reasons = []

    bullish_score = 0

    bearish_score = 0

    # =====================================
    # RSI ANALYSIS
    # =====================================
    rsi = market.get("rsi")

    if rsi is not None:

        if rsi < 30:

            bullish_score += 1

            reasons.append(
                "RSI indicates oversold conditions"
            )

        elif rsi > 70:

            bearish_score += 1

            reasons.append(
                "RSI indicates overbought conditions"
            )

    # =====================================
    # MACD ANALYSIS
    # =====================================
    macd_data = market.get(
        "macd",
        {}
    )

    macd_line = macd_data.get(
        "macd"
    )

    signal_line = macd_data.get(
        "signal"
    )

    histogram = macd_data.get(
        "histogram"
    )

    if (
        macd_line is not None and
        signal_line is not None
    ):

        if macd_line > signal_line:

            bullish_score += 1

            reasons.append(
                "MACD shows bullish momentum"
            )

        elif macd_line < signal_line:

            bearish_score += 1

            reasons.append(
                "MACD shows bearish momentum"
            )

    if histogram is not None:

        if histogram > 0:

            bullish_score += 1

            reasons.append(
                "MACD histogram is positive"
            )

        elif histogram < 0:

            bearish_score += 1

            reasons.append(
                "MACD histogram is negative"
            )

    # =====================================
    # CURRENT VALUATION ANALYSIS
    # =====================================
    pe_ratio = fundamentals.get(
        "pe_ratio"
    )

    forward_pe = fundamentals.get(
        "forward_pe"
    )

    if pe_ratio is not None:

        if pe_ratio < 20:

            bullish_score += 1

            reasons.append(
                "P/E ratio suggests reasonable valuation"
            )

        elif pe_ratio > 60:

            bearish_score += 1

            reasons.append(
                "P/E ratio suggests expensive valuation"
            )

    if (
        pe_ratio is not None and
        forward_pe is not None
    ):

        if forward_pe < pe_ratio:

            bullish_score += 1

            reasons.append(
                "Forward P/E suggests earnings growth"
            )

    # =====================================
    # REVENUE HISTORY ANALYSIS
    # =====================================
    revenue_history = fundamentals.get(
        "revenue_history",
        []
    )

    try:

        growth_years = 0

        decline_years = 0

        for i in range(
            len(revenue_history) - 1
        ):

            current = revenue_history[i]

            previous = revenue_history[i + 1]

            current_revenue = current.get(
                "revenue"
            )

            previous_revenue = previous.get(
                "revenue"
            )

            if (
                current_revenue is not None and
                previous_revenue is not None
            ):

                if current_revenue > previous_revenue:

                    growth_years += 1

                else:

                    decline_years += 1

        if growth_years >= 2:

            bullish_score += 2

            reasons.append(
                "Revenue has shown strong multi-year growth"
            )

        elif decline_years >= 2:

            bearish_score += 2

            reasons.append(
                "Revenue growth trend is weakening"
            )

    except Exception as e:

        print(
            f"Revenue analysis error: {e}"
        )

    # =====================================
    # EPS HISTORY ANALYSIS
    # =====================================
    eps_history = fundamentals.get(
        "eps_history",
        []
    )

    try:

        eps_growth_years = 0

        eps_decline_years = 0

        for i in range(
            len(eps_history) - 1
        ):

            current = eps_history[i]

            previous = eps_history[i + 1]

            current_eps = current.get(
                "eps"
            )

            previous_eps = previous.get(
                "eps"
            )

            if (
                current_eps is not None and
                previous_eps is not None
            ):

                if current_eps > previous_eps:

                    eps_growth_years += 1

                else:

                    eps_decline_years += 1

        if eps_growth_years >= 2:

            bullish_score += 2

            reasons.append(
                "EPS has improved consistently"
            )

        elif eps_decline_years >= 2:

            bearish_score += 2

            reasons.append(
                "EPS trend is weakening"
            )

    except Exception as e:

        print(
            f"EPS analysis error: {e}"
        )

    # =====================================
    # PROFIT MARGIN HISTORY
    # =====================================
    margin_history = fundamentals.get(
        "profit_margin_history",
        []
    )

    try:

        improving_margins = 0

        weakening_margins = 0

        for i in range(
            len(margin_history) - 1
        ):

            current = margin_history[i]

            previous = margin_history[i + 1]

            current_margin = current.get(
                "profit_margin"
            )

            previous_margin = previous.get(
                "profit_margin"
            )

            if (
                current_margin is not None and
                previous_margin is not None
            ):

                if current_margin > previous_margin:

                    improving_margins += 1

                else:

                    weakening_margins += 1

        if improving_margins >= 2:

            bullish_score += 2

            reasons.append(
                "Profit margins are improving"
            )

        elif weakening_margins >= 2:

            bearish_score += 2

            reasons.append(
                "Profit margins are weakening"
            )

    except Exception as e:

        print(
            f"Margin analysis error: {e}"
        )

    # =====================================
    # OPERATING MARGIN HISTORY
    # =====================================
    operating_margin_history = fundamentals.get(
        "operating_margin_history",
        []
    )

    try:

        improving_operating = 0

        weakening_operating = 0

        for i in range(
            len(operating_margin_history) - 1
        ):

            current = operating_margin_history[i]

            previous = operating_margin_history[i + 1]

            current_margin = current.get(
                "operating_margin"
            )

            previous_margin = previous.get(
                "operating_margin"
            )

            if (
                current_margin is not None and
                previous_margin is not None
            ):

                if current_margin > previous_margin:

                    improving_operating += 1

                else:

                    weakening_operating += 1

        if improving_operating >= 2:

            bullish_score += 2

            reasons.append(
                "Operating margins are improving"
            )

        elif weakening_operating >= 2:

            bearish_score += 2

            reasons.append(
                "Operating margins are weakening"
            )

    except Exception as e:

        print(
            f"Operating margin analysis error: {e}"
        )

    # =====================================
    # ROE HISTORY ANALYSIS
    # =====================================
    roe_history = fundamentals.get(
        "roe_history",
        []
    )

    try:

        improving_roe = 0

        weakening_roe = 0

        for i in range(
            len(roe_history) - 1
        ):

            current = roe_history[i]

            previous = roe_history[i + 1]

            current_roe = current.get(
                "return_on_equity"
            )

            previous_roe = previous.get(
                "return_on_equity"
            )

            if (
                current_roe is not None and
                previous_roe is not None
            ):

                if current_roe > previous_roe:

                    improving_roe += 1

                else:

                    weakening_roe += 1

        if improving_roe >= 2:

            bullish_score += 2

            reasons.append(
                "Return on equity is improving"
            )

        elif weakening_roe >= 2:

            bearish_score += 2

            reasons.append(
                "Return on equity is weakening"
            )

    except Exception as e:

        print(
            f"ROE analysis error: {e}"
        )

    # =====================================
    # DEBT TO EQUITY HISTORY
    # =====================================
    debt_history = fundamentals.get(
        "debt_to_equity_history",
        []
    )

    try:

        improving_debt = 0

        worsening_debt = 0

        for i in range(
            len(debt_history) - 1
        ):

            current = debt_history[i]

            previous = debt_history[i + 1]

            current_debt = current.get(
                "debt_to_equity"
            )

            previous_debt = previous.get(
                "debt_to_equity"
            )

            if (
                current_debt is not None and
                previous_debt is not None
            ):

                if current_debt < previous_debt:

                    improving_debt += 1

                else:

                    worsening_debt += 1

        if improving_debt >= 2:

            bullish_score += 1

            reasons.append(
                "Debt levels are improving"
            )

        elif worsening_debt >= 2:

            bearish_score += 2

            reasons.append(
                "Debt burden is increasing"
            )

    except Exception as e:

        print(
            f"Debt analysis error: {e}"
        )

    # =====================================
    # FREE CASH FLOW HISTORY
    # =====================================
    cashflow_history = fundamentals.get(
        "free_cashflow_history",
        []
    )

    try:

        improving_cashflow = 0

        weakening_cashflow = 0

        for i in range(
            len(cashflow_history) - 1
        ):

            current = cashflow_history[i]

            previous = cashflow_history[i + 1]

            current_cash = current.get(
                "free_cashflow"
            )

            previous_cash = previous.get(
                "free_cashflow"
            )

            if (
                current_cash is not None and
                previous_cash is not None
            ):

                if current_cash > previous_cash:

                    improving_cashflow += 1

                else:

                    weakening_cashflow += 1

        if improving_cashflow >= 2:

            bullish_score += 2

            reasons.append(
                "Free cash flow is improving"
            )

        elif weakening_cashflow >= 2:

            bearish_score += 2

            reasons.append(
                "Free cash flow is weakening"
            )

    except Exception as e:

        print(
            f"Cashflow analysis error: {e}"
        )

    # =====================================
    # DIVIDEND ANALYSIS
    # =====================================
    dividend_yield = fundamentals.get(
        "dividend_yield"
    )

    payout_ratio = fundamentals.get(
        "payout_ratio"
    )

    dividend_history = fundamentals.get(
        "dividend_history",
        []
    )

    if dividend_yield is not None:

        if (
            dividend_yield > 0.02 and
            payout_ratio is not None and
            payout_ratio < 0.7
        ):

            bullish_score += 1

            reasons.append(
                "Healthy dividend profile"
            )

        elif (
            payout_ratio is not None and
            payout_ratio > 1
        ):

            bearish_score += 1

            reasons.append(
                "Dividend payout may be unsustainable"
            )

    try:

        increasing_dividends = 0

        decreasing_dividends = 0

        for i in range(
            len(dividend_history) - 1
        ):

            current = dividend_history[i]

            previous = dividend_history[i + 1]

            current_dividend = current.get(
                "annual_dividend"
            )

            previous_dividend = previous.get(
                "annual_dividend"
            )

            if (
                current_dividend is not None and
                previous_dividend is not None
            ):

                if current_dividend > previous_dividend:

                    increasing_dividends += 1

                else:

                    decreasing_dividends += 1

        if increasing_dividends >= 2:

            bullish_score += 1

            reasons.append(
                "Dividend payments are growing consistently"
            )

        elif decreasing_dividends >= 2:

            bearish_score += 1

            reasons.append(
                "Dividend payments are weakening"
            )

    except Exception as e:

        print(
            f"Dividend analysis error: {e}"
        )

    # =====================================
    # NEWS SENTIMENT ANALYSIS
    # =====================================
    positive_news = 0

    negative_news = 0

    for article in news:

        sentiment = article.get(
            "sentiment",
            ""
        ).lower()

        if sentiment == "positive":

            positive_news += 1

        elif sentiment == "negative":

            negative_news += 1

    if positive_news > negative_news:

        bullish_score += 1

        reasons.append(
            "News sentiment is positive"
        )

    elif negative_news > positive_news:

        bearish_score += 1

        reasons.append(
            "News sentiment is negative"
        )

    # =====================================
    # FINAL BIAS
    # =====================================
    if bullish_score > bearish_score:

        bias = "Bullish"

    elif bearish_score > bullish_score:

        bias = "Bearish"

    else:

        bias = "Neutral"

    # =====================================
    # CONFIDENCE SCORE
    # =====================================
    total_signals = (
        bullish_score +
        bearish_score
    )

    if total_signals > 0:

        confidence = round(

            max(
                bullish_score,
                bearish_score
            ) / total_signals,

            2
        )

    else:

        confidence = 0

    # =====================================
    # STORE RESULTS
    # =====================================
    return {"strategy_analysis":{

        "overall_bias": bias,

        "confidence": confidence,

        "bullish_score": bullish_score,

        "bearish_score": bearish_score,

        "total_signals": total_signals,

        "reasons": reasons}
    }

