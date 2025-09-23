from models import db, User, Movie


class DataManager:
    """
    Handles database operations for users and movies.
    """

    def create_user(self, name):
        """Create and save a new user."""
        user = User(name=name)
        db.session.add(user)
        db.session.commit()

    def get_users(self):
        """Return all users."""
        return User.query.all()

    def get_movies(self, user_id):
        """Return all movies for a specific user."""
        return Movie.query.filter_by(user_id=user_id).all()

    def add_movie(self, movie):
        """Add a movie to the database."""
        db.session.add(movie)
        db.session.commit()

    def update_movie(self, movie_id, new_title):
        """Update the title of a movie."""
        movie = Movie.query.get(movie_id)
        if movie:
            movie.name = new_title
            db.session.commit()

    def delete_movie(self, movie_id):
        """Delete a movie from the database."""
        movie = Movie.query.get(movie_id)
        if movie:
            db.session.delete(movie)
            db.session.commit()

    def rate_movie(self, movie_id, rating):
        """
        Save a star rating (1-5) for a movie.
        """
        movie = Movie.query.get(movie_id)
        if movie and isinstance(rating, int) and 1 <= rating <= 5:
            movie.rating = rating
            db.session.commit()
            return True
        return False
