from Backend.embeddings.bge_embedding import (

    BGEEmbedding

)
from Backend.Resilience.breakers import embedding_breaker

class EmbeddingService:

    def __init__(

            self

    ):

        self.embedding_model = (

            BGEEmbedding()

        )

    def embed(

            self,

            text

    ):
        return embedding_breaker.call( self.embedding_model.embed_text,

            text

        )

    def embed_batch(

            self,

            texts

    ):
        return self.embedding_model.embed_batch(

            texts

        )

    def dimension(

            self

    ):
        return self.embedding_model.dimension()