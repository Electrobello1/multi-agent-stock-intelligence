
from Backend.database.connection import Base, engine

# Import ALL SQLAlchemy models before create_all()
from Backend.database.user_table import User
from Backend.database.sessions_table import Session
from Backend.database.analysis import Analysis
from Backend.database.Analysis_vector import AnalysisVector
from Backend.database.email_verification import EmailVerification
from Backend.database.password_reset import PasswordResetToken


def init_database():
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")


if __name__ == "__main__":
    init_database()
