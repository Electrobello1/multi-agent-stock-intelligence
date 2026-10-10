
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError



from Backend.database.Analysis_vector import AnalysisVector
from Backend.embeddings.embedding_service import EmbeddingService
from Backend.exceptions import VectorNotFoundError


logger = logging.getLogger(__name__)


class VectorMemory:

    def __init__(
            self,
            db: Session,
            embedding_service: EmbeddingService
    ):
        self.db = db
        self.embedding_service = embedding_service

    def upsert_vector(
            self,
            analysis_id,
            session_id,
            user_id,
            embedded_text: str
    ):
        """
        Insert a new vector or update an existing one.

        This operation is idempotent.
        """

        vector = self.embedding_service.embed(
            embedded_text
        )

        try:

            record = (

                self.db.query(
                    AnalysisVector
                )

                .filter(
                    AnalysisVector.analysis_id == analysis_id
                )

                .first()

            )

            if record:

                record.embedded_text = embedded_text
                record.embedding = vector
                record.session_id = session_id
                record.user_id = user_id

            else:

                record = AnalysisVector(

                    analysis_id=analysis_id,

                    session_id=session_id,

                    user_id=user_id,

                    embedded_text=embedded_text,

                    embedding=vector

                )

                self.db.add(record)

            self.db.commit()

            self.db.refresh(record)

            return record.id

        except SQLAlchemyError as e:

            self.db.rollback()

            logger.exception(e)

            raise

    def search_similar(
            self,
            user_id,
            query: str,
            session_id=None,
            top_k: int = 5
    ):
        """
        Perform semantic similarity search using pgvector cosine distance.
        """

        query_vector = self.embedding_service.embed(
            query
        )

        try:

            statement = (

                self.db.query(

                    AnalysisVector,

                    AnalysisVector.embedding
                    .cosine_distance(query_vector)
                    .label("distance")

                )

                .filter(

                    AnalysisVector.user_id == user_id

                )

            )

            if session_id is not None:
                statement = statement.filter(

                    AnalysisVector.session_id == session_id

                )

            results = (

                statement

                .order_by("distance")

                .limit(top_k)

                .all()

            )

            return [

                {

                    "analysis_id": row.analysis_id,

                    "session_id": row.session_id,

                    "user_id": row.user_id,

                    "embedded_text": row.embedded_text,

                    "score": round(
                        1 - distance,
                        4
                    ),

                    "created_at": row.created_at

                }

                for row, distance in results

            ]

        except SQLAlchemyError as e:

            logger.exception(e)

            raise
    def delete_vector(
            self,
            analysis_id
    ):
        """
        Delete a stored embedding.
        """

        try:

            record = (

                self.db.query(

                    AnalysisVector

                )

                .filter(

                    AnalysisVector.analysis_id == analysis_id

                )

                .first()

            )

            if record is None:

                raise VectorNotFoundError(

                    "Vector not found."

                )

            self.db.delete(record)

            self.db.commit()

            return True

        except SQLAlchemyError as e:

            self.db.rollback()

            logger.exception(e)

            raise

    def get_vector(
            self,
            analysis_id
    ):
        """
        Retrieve a stored vector record.
        """

        record = (

            self.db.query(

                AnalysisVector

            )

            .filter(

                AnalysisVector.analysis_id == analysis_id

            )

            .first()

        )

        if record is None:

            raise VectorNotFoundError(

                "Vector not found."

            )

        return {

            "analysis_id": record.analysis_id,

            "session_id": record.session_id,

            "user_id": record.user_id,

            "embedded_text": record.embedded_text,

            "created_at": record.created_at

        }