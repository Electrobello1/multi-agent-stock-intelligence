import os

from massive import RESTClient

from dotenv import load_dotenv

from Backend.Resilience.breakers import (
    news_breaker
)


load_dotenv()


class MassiveNewsProvider:

    def __init__(self):

        self.client = RESTClient(
            os.getenv("POLYGON_API_KEY")
        )

    # =====================================
    # GET COMPANY NEWS
    # =====================================

    def get_news(
        self,
        ticker,
        limit=10
    ):

        news_items = []

        try:

            articles = news_breaker.call(
                self.client.list_ticker_news,
                ticker=ticker,
                limit=limit
            )

            for i, article in enumerate(
                articles
            ):

                if i >= limit:
                    break

                news_items.append(
                    {
                        "title": article.title,

                        "published_utc": (
                            article.published_utc
                        ),

                        "article_url": (
                            article.article_url
                        ),

                        "author": article.author,

                        "description": (
                            article.description
                        ),

                        "keywords": article.keywords,

                        "insights": article.insights,

                        "publisher": {
                            "name": (
                                article.publisher.name
                            ),

                            "homepage_url": (
                                article.publisher.homepage_url
                            )
                        }
                    }
                )

            return news_items

        except Exception as e:

            raise Exception(
                f"Massive News Error: {e}"
            )
