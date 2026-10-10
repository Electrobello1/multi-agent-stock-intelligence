from sentence_transformers import (
    SentenceTransformer
)

from Backend.embeddings.base_embedding import (
    BaseEmbedding
)
class BGEEmbedding(

    BaseEmbedding

):

    MODEL_NAME = (
        "BAAI/bge-small-en-v1.5"
    )

    def __init__(

            self

    ):

        self.model = SentenceTransformer(

            self.MODEL_NAME

        )

    def embed_text(

            self,

            text: str

    ):
        return self.model.encode(

            text,

            normalize_embeddings=True

        ).tolist()

    def embed_batch(

            self,

            texts: list[str]

    ):
        return self.model.encode(

            texts,

            normalize_embeddings=True

        ).tolist()

    def dimension(

            self

    ):
        return self.model.get_embedding_dimension()


