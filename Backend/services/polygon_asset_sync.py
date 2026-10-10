import os
import time
import requests

from dotenv import load_dotenv

from Backend.database.connection import SessionLocal
from Backend.database.Asset_table import Asset


load_dotenv()

POLYGON_API_KEY = os.getenv(
    "POLYGON_API_KEY"
)


class PolygonAssetSync:

    def __init__(self):

        self.base_url = (
            "https://api.polygon.io/v3/reference/tickers"
        )

    # ==========================================
    # FETCH ALL ASSETS WITH PAGINATION
    # ==========================================
    def fetch_assets(self):

        all_assets = []

        cursor = None

        while True:

            params = {

                "market": "stocks",

                "active": "true",

                "limit": 1000,

                "apiKey": POLYGON_API_KEY
            }

            # pagination cursor
            if cursor:

                params["cursor"] = cursor

            print("\nFETCHING PAGE...")

            response = requests.get(
                self.base_url,
                params=params
            )

            # --------------------------------
            # RATE LIMIT HANDLING
            # --------------------------------
            if response.status_code == 429:

                print(
                    "RATE LIMITED - WAITING 60 SECONDS..."
                )

                time.sleep(120)

                continue

            data = response.json()

            # DEBUGGING
            print("STATUS CODE:", response.status_code)

            results = data.get(
                "results",
                []
            )

            print(
                "DOWNLOADED:",
                len(results)
            )

            # stop if empty
            if not results:

                print("NO MORE RESULTS")

                break

            all_assets.extend(results)

            print(
                "TOTAL SO FAR:",
                len(all_assets)
            )

            next_url = data.get(
                "next_url"
            )

            print("NEXT URL:")
            print(next_url)

            # --------------------------------
            # STOP IF NO NEXT PAGE
            # --------------------------------
            if not next_url:

                print("PAGINATION COMPLETE")

                break

            # --------------------------------
            # EXTRACT CURSOR
            # --------------------------------
            if "cursor=" in next_url:

                cursor = next_url.split(
                    "cursor="
                )[1].split("&")[0]

            else:

                print(
                    "CURSOR EXTRACTION FAILED"
                )

                break

            # --------------------------------
            # FREE TIER RATE LIMIT PROTECTION
            # --------------------------------
            time.sleep(15)

        return all_assets

    # ==========================================
    # SAVE TO DATABASE
    # ==========================================
    def save_assets(self, assets):

        db = SessionLocal()

        try:

            for asset in assets:

                symbol = asset.get(
                    "ticker"
                )

                company_name = asset.get(
                    "name"
                )

                exchange = asset.get(
                    "primary_exchange"
                )

                asset_type = asset.get(
                    "type"
                )

                # skip empty
                if not symbol:

                    continue

                # prevent duplicates
                exists = db.query(
                    Asset
                ).filter(
                    Asset.symbol == symbol
                ).first()

                if exists:

                    continue

                db_asset = Asset(

                    symbol=symbol,

                    company_name=company_name,

                    exchange=exchange,

                    asset_type=asset_type
                )

                db.add(db_asset)

            db.commit()

            print(
                f"\nSAVED {len(assets)} ASSETS"
            )

        finally:

            db.close()

    # ==========================================
    # MAIN RUNNER
    # ==========================================
    def run(self):

        assets = self.fetch_assets()

        print(
            f"\nTOTAL DOWNLOADED: {len(assets)}"
        )

        self.save_assets(assets)


if __name__ == "__main__":

    sync = PolygonAssetSync()

    sync.run()