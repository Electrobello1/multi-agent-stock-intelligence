

import os
import requests
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
from Backend.Resilience.breakers import (
    yahoo_fundamental_breaker,
    alphavantage_fundamental_breaker,
)

load_dotenv()


def safe_float(value):
    try:

        if value in [
            None,
            "None",
            "",
            "null",
            "-",
            "NaN"
        ]:
            return None

        return float(value)

    except:

        return None

class FundamentalsProvider:

    def __init__(self):

        self.api_key = os.getenv(
            "ALPHA_VANTAGE_API_KEY"
        )

    # ======================================
    # MAIN ENTRY
    # ======================================
    def get_fundamentals(
            self,
            ticker
    ):

        # ----------------------------------
        # TRY YAHOO FIRST
        # ----------------------------------
        try:

            print(
                "Using Yahoo Fundamentals"
            )

            return yahoo_fundamental_breaker.call(
                self._get_yahoo_fundamentals,
                ticker
            )

        except Exception as e:

            print(
                f"Yahoo failed: {e}"
            )

        # ----------------------------------
        # FALLBACK TO ALPHA VANTAGE
        # ----------------------------------
        try:

            print(
                "Using AlphaVantage Fundamentals"
            )

            return alphavantage_fundamental_breaker.call(
                self.get_Alphavantage_fundamentals,
                ticker
            )

        except Exception as e:

            print(
                f"AlphaVantage failed: {e}"
            )

        raise Exception(
            "All fundamentals providers failed"
        )

        # ====================================
        # YAHOO FUNDAMENTALS
        # =====================================

    def _get_yahoo_fundamentals(
            self,
            ticker
    ):

        stock = yf.Ticker(ticker)

        info = stock.info

        income_stmt = stock.financials

        balance_sheet = stock.balance_sheet

        cashflow_stmt = stock.cashflow

        # =====================================
        # HISTORICAL STORAGE
        # =====================================
        revenue_history = []

        eps_history = []

        profit_margin_history = []

        operating_margin_history = []

        roe_history = []

        debt_to_equity_history = []

        free_cashflow_history = []

        dividend_history = []

        # =====================================
        # DIVIDEND HISTORY
        # =====================================
        try:

            dividends = stock.dividends

            yearly_dividends = {}

            for date, value in dividends.items():

                year = str(date.year)

                if year not in yearly_dividends:
                    yearly_dividends[year] = 0

                yearly_dividends[year] += float(value)

            sorted_years = sorted(
                yearly_dividends.keys(),
                reverse=True
            )

            for year in sorted_years[:5]:
                dividend_history.append({

                    "year": year,

                    "annual_dividend":
                        yearly_dividends[year]
                })

        except Exception as e:

            print(
                f"Dividend history error: {e}"
            )

        # =====================================
        # PROCESS FINANCIAL HISTORY
        # =====================================
        try:

            years = income_stmt.columns[:5]

            for column in years:

                year = str(column.year)

                # ---------------------------------
                # REVENUE
                # ---------------------------------
                revenue = None

                if (
                        "Total Revenue"
                        in income_stmt.index
                ):
                    revenue = income_stmt.loc[
                        "Total Revenue",
                        column
                    ]

                # ---------------------------------
                # NET INCOME
                # ---------------------------------
                net_income = None

                if (
                        "Net Income"
                        in income_stmt.index
                ):
                    net_income = income_stmt.loc[
                        "Net Income",
                        column
                    ]

                # ---------------------------------
                # OPERATING INCOME
                # ---------------------------------
                operating_income = None

                if (
                        "Operating Income"
                        in income_stmt.index
                ):
                    operating_income = income_stmt.loc[
                        "Operating Income",
                        column
                    ]

                # ---------------------------------
                # SHAREHOLDER EQUITY
                # ---------------------------------
                shareholder_equity = None

                if (
                        "Stockholders Equity"
                        in balance_sheet.index
                ):
                    shareholder_equity = balance_sheet.loc[
                        "Stockholders Equity",
                        column
                    ]

                # ---------------------------------
                # TOTAL DEBT
                # ---------------------------------
                total_debt = None

                if (
                        "Total Debt"
                        in balance_sheet.index
                ):
                    total_debt = balance_sheet.loc[
                        "Total Debt",
                        column
                    ]

                # ---------------------------------
                # FREE CASH FLOW
                # ---------------------------------
                free_cashflow = None

                if (
                        "Free Cash Flow"
                        in cashflow_stmt.index
                ):
                    free_cashflow = cashflow_stmt.loc[
                        "Free Cash Flow",
                        column
                    ]

                # ---------------------------------
                # CLEAN NaN VALUES
                # ---------------------------------
                values = [
                    revenue,
                    net_income,
                    operating_income,
                    shareholder_equity,
                    total_debt,
                    free_cashflow
                ]

                cleaned = []

                for value in values:

                    if pd.isna(value):

                        cleaned.append(None)

                    else:

                        cleaned.append(value)

                (
                    revenue,
                    net_income,
                    operating_income,
                    shareholder_equity,
                    total_debt,
                    free_cashflow
                ) = cleaned

                # =================================
                # CALCULATED METRICS
                # =================================

                # ---------------------------------
                # EPS
                # ---------------------------------
                eps = None

                shares = info.get(
                    "sharesOutstanding"
                )

                if (
                        net_income and
                        shares
                ):

                    try:

                        eps = (
                                net_income / shares
                        )

                    except:
                        pass

                # ---------------------------------
                # PROFIT MARGIN
                # ---------------------------------
                profit_margin = None

                if (
                        revenue and
                        net_income
                ):

                    try:

                        profit_margin = (
                                net_income / revenue
                        )

                    except:
                        pass

                # ---------------------------------
                # OPERATING MARGIN
                # ---------------------------------
                operating_margin = None

                if (
                        revenue and
                        operating_income
                ):

                    try:

                        operating_margin = (
                                operating_income /
                                revenue
                        )

                    except:
                        pass

                # ---------------------------------
                # RETURN ON EQUITY
                # ---------------------------------
                roe = None

                if (
                        net_income and
                        shareholder_equity
                ):

                    try:

                        roe = (
                                net_income /
                                shareholder_equity
                        )

                    except:
                        pass

                # ---------------------------------
                # DEBT TO EQUITY
                # ---------------------------------
                debt_to_equity = None

                if (
                        total_debt and
                        shareholder_equity
                ):

                    try:

                        debt_to_equity = (
                                                 total_debt /
                                                 shareholder_equity
                                         ) * 100

                    except:
                        pass

                # =================================
                # STORE HISTORIES
                # =================================

                revenue_history.append({

                    "year": year,

                    "revenue": revenue,

                    "net_income": net_income
                })

                eps_history.append({

                    "year": year,

                    "eps": eps
                })

                profit_margin_history.append({

                    "year": year,

                    "profit_margin":
                        profit_margin
                })

                operating_margin_history.append({

                    "year": year,

                    "operating_margin":
                        operating_margin
                })

                roe_history.append({

                    "year": year,

                    "return_on_equity":
                        roe
                })

                debt_to_equity_history.append({

                    "year": year,

                    "debt_to_equity":
                        debt_to_equity
                })

                free_cashflow_history.append({

                    "year": year,

                    "free_cashflow":
                        free_cashflow
                })

        except Exception as e:

            print(
                f"Historical analysis error: {e}"
            )

        # =====================================
        # RETURN STRUCTURED DATA
        # =====================================
        return {

            "provider": "Yahoo",

            # =================================
            # COMPANY INFO
            # =================================
            "company_name": info.get(
                "longName"
            ),

            "sector": info.get(
                "sector"
            ),

            "industry": info.get(
                "industry"
            ),

            # =================================
            # CURRENT SNAPSHOT METRICS
            # =================================
            "market_cap": info.get(
                "marketCap"
            ),

            "pe_ratio": info.get(
                "trailingPE"
            ),

            "forward_pe": info.get(
                "forwardPE"
            ),

            "eps": info.get(
                "trailingEps"
            ),

            "profit_margin": info.get(
                "profitMargins"
            ),

            "operating_margin": info.get(
                "operatingMargins"
            ),

            "return_on_equity": info.get(
                "returnOnEquity"
            ),

            "debt_to_equity": info.get(
                "debtToEquity"
            ),

            "free_cashflow": info.get(
                "freeCashflow"
            ),

            "revenue": info.get(
                "totalRevenue"
            ),

            # =================================
            # DIVIDEND METRICS
            # =================================
            "dividend_yield": info.get(
                "dividendYield"
            ),

            "dividend_rate": info.get(
                "dividendRate"
            ),

            "payout_ratio": info.get(
                "payoutRatio"
            ),

            # =================================
            # HISTORICAL METRICS
            # =================================
            "revenue_history":
                revenue_history,

            "eps_history":
                eps_history,

            "profit_margin_history":
                profit_margin_history,

            "operating_margin_history":
                operating_margin_history,

            "roe_history":
                roe_history,

            "debt_to_equity_history":
                debt_to_equity_history,

            "free_cashflow_history":
                free_cashflow_history,

            "dividend_history":
                dividend_history
        }
    # ======================================
    # POLYGON FUNDAMENTALS
    # ======================================




    def get_Alphavantage_fundamentals(
            self,
            ticker
    ):

        # ---------------------------------
        # BASE URL
        # ---------------------------------
        base_url = (
            "https://www.alphavantage.co/query"
        )

        # =====================================
        # COMPANY OVERVIEW
        # =====================================
        overview_params = {

            "function": "OVERVIEW",

            "symbol": ticker,

            "apikey": self.api_key
        }

        overview_response = requests.get(
            base_url,
            params=overview_params
        )

        overview = overview_response.json()

        # =====================================
        # VALIDATION
        # =====================================
        if not overview:
            raise Exception(
                "Empty Alpha Vantage response"
            )

        if "Note" in overview:
            raise Exception(
                overview["Note"]
            )

        if "Symbol" not in overview:
            raise Exception(
                "Invalid Alpha Vantage response"
            )

        # =====================================
        # INCOME STATEMENT
        # =====================================
        income_params = {

            "function": "INCOME_STATEMENT",

            "symbol": ticker,

            "apikey": self.api_key
        }

        income_response = requests.get(
            base_url,
            params=income_params
        )

        income_data = income_response.json()

        # =====================================
        # BALANCE SHEET
        # =====================================
        balance_params = {

            "function": "BALANCE_SHEET",

            "symbol": ticker,

            "apikey": self.api_key
        }

        balance_response = requests.get(
            base_url,
            params=balance_params
        )

        balance_data = balance_response.json()

        # =====================================
        # CASH FLOW
        # =====================================
        cashflow_params = {

            "function": "CASH_FLOW",

            "symbol": ticker,

            "apikey": self.api_key
        }

        cashflow_response = requests.get(
            base_url,
            params=cashflow_params
        )

        cashflow_data = cashflow_response.json()

        # =====================================
        # HISTORICAL STORAGE
        # =====================================
        revenue_history = []

        eps_history = []

        profit_margin_history = []

        operating_margin_history = []

        roe_history = []

        debt_to_equity_history = []

        free_cashflow_history = []

        dividend_history = []

        # =====================================
        # PROCESS HISTORICAL DATA
        # =====================================
        try:

            income_reports = income_data.get(
                "annualReports",
                []
            )

            balance_reports = balance_data.get(
                "annualReports",
                []
            )

            cashflow_reports = cashflow_data.get(
                "annualReports",
                []
            )

            for i in range(
                    min(
                        5,
                        len(income_reports)
                    )
            ):

                income_report = income_reports[i]

                balance_report = (
                    balance_reports[i]
                    if i < len(balance_reports)
                    else {}
                )

                cashflow_report = (
                    cashflow_reports[i]
                    if i < len(cashflow_reports)
                    else {}
                )

                year = income_report.get(
                    "fiscalDateEnding",
                    ""
                )[:4]

                # ---------------------------------
                # REVENUE
                # ---------------------------------
                revenue = safe_float(
                    income_report.get(
                        "totalRevenue"
                    )
                )

                # ---------------------------------
                # NET INCOME
                # ---------------------------------
                net_income = safe_float(
                    income_report.get(
                        "netIncome"
                    )
                )

                # ---------------------------------
                # OPERATING INCOME
                # ---------------------------------
                operating_income = safe_float(
                    income_report.get(
                        "operatingIncome"
                    )
                )

                # ---------------------------------
                # SHAREHOLDER EQUITY
                # ---------------------------------
                shareholder_equity = safe_float(
                    balance_report.get(
                        "totalShareholderEquity"
                    )
                )

                # ---------------------------------
                # TOTAL DEBT
                # ---------------------------------
                total_debt = safe_float(
                    balance_report.get(
                        "totalLiabilities"
                    )
                )

                # ---------------------------------
                # FREE CASH FLOW
                # ---------------------------------
                operating_cashflow = safe_float(
                    cashflow_report.get(
                        "operatingCashflow"
                    )
                )

                capital_expenditure = safe_float(
                    cashflow_report.get(
                        "capitalExpenditures"
                    )
                )

                free_cashflow = None

                try:

                    if (
                            operating_cashflow is not None and
                            capital_expenditure is not None
                    ):
                        free_cashflow = (
                                operating_cashflow -
                                abs(capital_expenditure)
                        )

                except:
                    pass

                # =================================
                # CALCULATED METRICS
                # =================================

                # ---------------------------------
                # EPS
                # ---------------------------------
                eps = None

                shares = safe_float(
                    overview.get(
                        "SharesOutstanding"
                    )
                )

                try:

                    if shares and net_income:
                        eps = (
                                net_income /
                                shares
                        )

                except:
                    pass

                # ---------------------------------
                # PROFIT MARGIN
                # ---------------------------------
                profit_margin = None

                try:

                    if revenue and net_income:
                        profit_margin = (
                                net_income / revenue
                        )

                except:
                    pass

                # ---------------------------------
                # OPERATING MARGIN
                # ---------------------------------
                operating_margin = None

                try:

                    if revenue and operating_income:
                        operating_margin = (
                                operating_income /
                                revenue
                        )

                except:
                    pass

                # ---------------------------------
                # RETURN ON EQUITY
                # ---------------------------------
                roe = None

                try:

                    if (
                            net_income and
                            shareholder_equity
                    ):
                        roe = (
                                net_income /
                                shareholder_equity
                        )

                except:
                    pass

                # ---------------------------------
                # DEBT TO EQUITY
                # ---------------------------------
                debt_to_equity = None

                try:

                    if (
                            total_debt and
                            shareholder_equity
                    ):
                        debt_to_equity = (
                                                 total_debt /
                                                 shareholder_equity
                                         ) * 100

                except:
                    pass

                # =================================
                # STORE HISTORIES
                # =================================

                revenue_history.append({

                    "year": year,

                    "revenue": revenue,

                    "net_income": net_income
                })

                eps_history.append({

                    "year": year,

                    "eps": eps
                })

                profit_margin_history.append({

                    "year": year,

                    "profit_margin":
                        profit_margin
                })

                operating_margin_history.append({

                    "year": year,

                    "operating_margin":
                        operating_margin
                })

                roe_history.append({

                    "year": year,

                    "return_on_equity":
                        roe
                })

                debt_to_equity_history.append({

                    "year": year,

                    "debt_to_equity":
                        debt_to_equity
                })

                free_cashflow_history.append({

                    "year": year,

                    "free_cashflow":
                        free_cashflow
                })

        except Exception as e:

            print(
                f"Historical analysis error: {e}"
            )

        # =====================================
        # DIVIDEND HISTORY
        # =====================================
        try:

            dividend_per_share = safe_float(
                overview.get(
                    "DividendPerShare"
                )
            )

            if dividend_per_share:

                for report in revenue_history:
                    dividend_history.append({

                        "year": report["year"],

                        "annual_dividend":
                            dividend_per_share
                    })

        except Exception as e:

            print(
                f"Dividend history error: {e}"
            )

        # =====================================
        # RETURN STRUCTURED DATA
        # =====================================
        return {

            "provider": "AlphaVantage",

            # =================================
            # COMPANY INFO
            # =================================
            "company_name": overview.get(
                "Name"
            ),

            "sector": overview.get(
                "Sector"
            ),

            "industry": overview.get(
                "Industry"
            ),

            "description": overview.get(
                "Description"
            ),

            "exchange": overview.get(
                "Exchange"
            ),

            "currency": overview.get(
                "Currency"
            ),

            "country": overview.get(
                "Country"
            ),

            # =================================
            # CURRENT SNAPSHOT METRICS
            # =================================
            "market_cap": safe_float(
                overview.get(
                    "MarketCapitalization"
                )
            ),

            "pe_ratio": safe_float(
                overview.get(
                    "PERatio"
                )
            ),

            "peg_ratio": safe_float(
                overview.get(
                    "PEGRatio"
                )
            ),

            "forward_pe": safe_float(
                overview.get(
                    "ForwardPE"
                )
            ),

            "price_to_book": safe_float(
                overview.get(
                    "PriceToBookRatio"
                )
            ),

            "eps": safe_float(
                overview.get(
                    "EPS"
                )
            ),

            "profit_margin": safe_float(
                overview.get(
                    "ProfitMargin"
                )
            ),

            "operating_margin": safe_float(
                overview.get(
                    "OperatingMarginTTM"
                )
            ),

            "return_on_equity": safe_float(
                overview.get(
                    "ReturnOnEquityTTM"
                )
            ),

            "return_on_assets": safe_float(
                overview.get(
                    "ReturnOnAssetsTTM"
                )
            ),

            "debt_to_equity": safe_float(
                overview.get(
                    "DebtToEquityRatio"
                )
            ),

            "revenue": safe_float(
                overview.get(
                    "RevenueTTM"
                )
            ),

            "gross_profit": safe_float(
                overview.get(
                    "GrossProfitTTM"
                )
            ),

            "dividend_yield": safe_float(
                overview.get(
                    "DividendYield"
                )
            ),

            "dividend_rate": safe_float(
                overview.get(
                    "DividendPerShare"
                )
            ),

            "payout_ratio": safe_float(
                overview.get(
                    "PayoutRatio"
                )
            ),

            "beta": safe_float(
                overview.get(
                    "Beta"
                )
            ),

            "analyst_target_price": safe_float(
                overview.get(
                    "AnalystTargetPrice"
                )
            ),

            # =================================
            # HISTORICAL METRICS
            # =================================
            "revenue_history":
                revenue_history,

            "eps_history":
                eps_history,

            "profit_margin_history":
                profit_margin_history,

            "operating_margin_history":
                operating_margin_history,

            "roe_history":
                roe_history,

            "debt_to_equity_history":
                debt_to_equity_history,

            "free_cashflow_history":
                free_cashflow_history,

            "dividend_history":
                dividend_history
        }


