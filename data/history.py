import sqlalchemy

from .db_session import SqlAlchemyBase


class History(SqlAlchemyBase):
    __tablename__ = 'history'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    moderator = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    action = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    user = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    book = sqlalchemy.Column(sqlalchemy.String, nullable=True, default=None)
