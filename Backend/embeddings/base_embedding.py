from abc import ABC
from abc import abstractmethod


class BaseEmbedding(ABC):

    @abstractmethod
    def embed_text(

            self,

            text: str

    ):

        pass

    @abstractmethod
    def embed_batch(

            self,

            texts: list[str]

    ):

        pass

    @abstractmethod
    def dimension(

            self

    ):

        pass