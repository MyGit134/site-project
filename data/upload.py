import sqlalchemy
from .db_session import SqlAlchemyBase


class Upload(SqlAlchemyBase):
    __tablename__ = 'files'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    book_name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    creator_email = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    file = sqlalchemy.Column(sqlalchemy.LargeBinary)
