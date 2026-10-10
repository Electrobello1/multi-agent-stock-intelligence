from abc import ABC, abstractmethod


class MarketDataProvider(ABC):

    @abstractmethod
    def get_price_history(
        self,
        ticker: str,
        period: str = "1y"
    ):
        pass