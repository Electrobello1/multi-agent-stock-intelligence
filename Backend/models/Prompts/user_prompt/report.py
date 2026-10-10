import json


def to_prompt(data):

    return json.dumps(

        data,

        indent=4,

        default=str,

        ensure_ascii=False

    )


def build_report_prompt(state):

    return f"""
Company

{to_prompt(state.get("resolved_asset", {}))}


Market Analysis

{to_prompt(state.get("market_analysis", {}))}


Fundamental Analysis

{to_prompt(state.get("fundamentals_analysis", {}))}


News Analysis

{to_prompt(state.get("news_analysis", []))}


Strategy Analysis

{to_prompt(state.get("strategy_analysis", {}))}


Generate a professional investment report.

The report should contain the following sections.

# Executive Summary

Provide a concise overview of the company.

# Technical Analysis
state the current price and sumarize the historical price. make sure it is concise.
Interpret:

- RSI
- MACD

Explain what they indicate.

# Fundamental Analysis

Discuss:


- Revenue Growth
- EPS Trend
- Profitability
- Operating Margins
- Return on Equity
- Debt Levels
- Free Cash Flow
- Dividend History
- Valuation

Highlight both strengths and weaknesses.

# News Analysis

Summarize the important recent news.

Explain how the news affects investors. please provide the aproprate links to the news for user verification

# Risks

List the key investment risks.

# Investor Suitability

Explain whether the stock is suitable for:

- Growth Investors
- Value Investors
- Dividend Investors
- Long-term Investors
- Short-term Traders

# Final Recommendation

Choose ONLY one:

- Strong Buy
- Buy
- Hold
- Sell
- Strong Sell

Explain the recommendation.

Include the confidence score from the strategy engine.

Finish with a concise conclusion and provide the following links so users can verify.https://finance.yahoo.com/ and https://www.alphavantage.co/
"""