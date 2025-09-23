from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """
    Represents a user of the MoviWeb app.
    Each user can have multiple favorite movies.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    movies = db.relationship('Movie', backref='user', lazy=True)


class Movie(db.Model):
    """
    Represents a movie added by a user.
    Contains details fetched from the OMDb API.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    director = db.Column(db.String(50))
    year = db.Column(db.String(10))  # String because OMDb sometimes returns ranges
    poster_url = db.Column(db.String(200))
    actors = db.Column(db.String(300))
    plot = db.Column(db.String(600))
    rating = db.Column(db.Integer)  # 1–10 stars
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
