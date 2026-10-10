import os
import time
import requests

from dotenv import load_dotenv

from Backend.database.connection import SessionLocal
from Backend.database.Asset_table import Asset


load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

BASE_URL = "https://api.polygon.io/v3/reference/tickers"


def sync_assets():

    if not POLYGON_API_KEY:
        raise RuntimeError(
            "POLYGON_API_KEY is not configured."
        )

    db = SessionLocal()

    inserted = 0
    updated = 0
    skipped = 0
    page = 0

    try:

        url = BASE_URL

        params = {
            "market": "stocks",
            "active": "true",
            "limit": 1000,
            "sort": "ticker",
            "order": "asc",
            "apiKey": POLYGON_API_KEY,
        }

        while url:

            page += 1

            print(
                f"Fetching page {page}..."
            )

            # -----------------------------
            # Provider request
            # -----------------------------

            while True:

                response = requests.get(
                    url,
                    params=params,
                    timeout=30,
                )

                if response.status_code == 429:

                    retry_after = (
                        response.headers.get(
                            "Retry-After"
                        )
                    )

                    wait_time = (
                        int(retry_after)
                        if retry_after
                        else 15
                    )

                    print(
                        "Rate limit reached. "
                        f"Waiting {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                    continue

                response.raise_for_status()

                break

            data = response.json()

            results = data.get(
                "results",
                []
            )

            # -----------------------------
            # Process assets
            # -----------------------------

            for item in results:

                symbol = item.get(
                    "ticker"
                )

                company_name = item.get(
                    "name"
                )

                exchange = item.get(
                    "primary_exchange"
                )

                asset_type = item.get(
                    "type"
                )

                # Symbol is the minimum
                # identifier we need.
                if not symbol:
                    skipped += 1
                    continue

                symbol = symbol.strip().upper()

                # -------------------------
                # Existing asset
                # -------------------------

                asset = (
                    db.query(Asset)
                    .filter(
                        Asset.symbol == symbol
                    )
                    .first()
                )

                if asset:

                    asset.company_name = (
                        company_name
                    )

                    asset.exchange = (
                        exchange
                    )

                    asset.asset_type = (
                        asset_type
                    )

                    updated += 1

                # -------------------------
                # New asset
                # -------------------------

                else:

                    asset = Asset(
                        symbol=symbol,
                        company_name=company_name,
                        exchange=exchange,
                        asset_type=asset_type,
                    )

                    db.add(asset)

                    inserted += 1

            # Commit after each page
            db.commit()

            print(
                f"Page {page} completed | "
                f"Processed: {len(results)} | "
                f"Inserted: {inserted} | "
                f"Updated: {updated}"
            )

            # -----------------------------
            # Pagination
            # -----------------------------

            next_url = data.get(
                "next_url"
            )

            if not next_url:
                break

            url = next_url

            # next_url already contains
            # cursor/filter information.
            params = {
                "apiKey": POLYGON_API_KEY
            }

            # Protect against rate limits
            time.sleep(15)

        print("\nAsset sync completed.")

        print(
            f"Inserted: {inserted}"
        )

        print(
            f"Updated: {updated}"
        )

        print(
            f"Skipped: {skipped}"
        )

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


if __name__ == "__main__":
    sync_assets()