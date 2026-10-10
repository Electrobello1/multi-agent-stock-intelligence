from rapidfuzz import fuzz

from Backend.database.connection import SessionLocal

from Backend.database.Asset_table import Asset


class ProductionTickerResolver:

    def __init__(self):

        self.db = SessionLocal()

        # high confidence aliases
        self.aliases = {

            "google": "GOOGL",

            "alphabet": "GOOGL",

            "facebook": "META",

            "meta": "META",

            "tesla": "TSLA",

            "apple": "AAPL",

            "amazon": "AMZN",

            "nvidia": "NVDA",

            "microsoft": "MSFT"
        }

    # ======================================
    # MAIN RESOLVE METHOD
    # ======================================
    def resolve(self, query):

        query = query.lower().strip()

        # ----------------------------------
        # 1. ALIAS MATCH
        # ----------------------------------
        if query in self.aliases:

            ticker = self.aliases[query]

            asset = self.db.query(
                Asset
            ).filter(
                Asset.symbol == ticker
            ).first()

            if asset:

                return self.format_result(
                    asset,
                    confidence=100,
                    method="alias"
                )

        # ----------------------------------
        # 2. EXACT SYMBOL MATCH
        # ----------------------------------
        symbol_match = self.db.query(
            Asset
        ).filter(
            Asset.symbol.ilike(query.upper())
        ).first()

        if symbol_match:

            return self.format_result(
                symbol_match,
                confidence=98,
                method="exact_symbol"
            )

        # ----------------------------------
        # 3. EXACT COMPANY NAME MATCH
        # ----------------------------------
        exact_name = self.db.query(
            Asset
        ).filter(
            Asset.company_name.ilike(f"%{query}%")
        ).first()

        if exact_name:

            return self.format_result(
                exact_name,
                confidence=95,
                method="company_name"
            )

        # ----------------------------------
        # 4. FUZZY MATCH
        # ----------------------------------
        all_assets = self.db.query(
            Asset
        ).all()

        best_score = 0

        best_asset = None

        for asset in all_assets:

            if not asset.company_name:

                continue

            score = fuzz.ratio(
                query,
                asset.company_name.lower()
            )

            if score > best_score:

                best_score = score

                best_asset = asset

        # confidence threshold
        if best_score >= 70:

            return self.format_result(
                best_asset,
                confidence=best_score,
                method="fuzzy"
            )

        raise Exception(
            f"Could not resolve asset: {query}"
        )

    # ======================================
    # FORMAT RESULT
    # ======================================
    def format_result(
        self,
        asset,
        confidence,
        method
    ):

        return {

            "ticker": asset.symbol,

            "company_name": asset.company_name,

            "exchange": asset.exchange,

            "asset_type": asset.asset_type,

            "confidence": confidence,

            "resolution_method": method
        }