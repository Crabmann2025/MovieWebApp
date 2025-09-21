from flask import Flask, request, redirect, url_for, render_template, flash
from models import db, Movie, User
from data_manager import DataManager
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moviweb.db'  # SQLite Database
app.config['SECRET_KEY'] = 'supersecretkey'  # Für flash-Meldungen
db.init_app(app)  # Connect Flask with database

data_manager = DataManager()

# Create database tables if not exist
with app.app_context():
    db.create_all()


# Routes

@app.route('/')
def index():
    """
    Home page: display all users and any flash messages.
    """
    users = data_manager.get_users()
    return render_template("index.html", users=users)


@app.route('/users', methods=['POST'])
def add_user():
    """
    Add a new user if it does not already exist.
    """
    name = request.form['name'].strip()
    if not name:
        flash("Please enter a valid name.", "error")
        return redirect(url_for('index'))

    existing_user = User.query.filter_by(name=name).first()
    if existing_user:
        flash(f"The user '{name}' already exists!", "error")
        return redirect(url_for('index'))

    data_manager.create_user(name)
    flash(f"User '{name}' has been created.", "success")
    return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def list_movies(user_id):
    """
    List all favorite movies of a specific user.
    """
    user = User.query.get(user_id)
    if not user:
        flash("User not found!", "error")
        return redirect(url_for('index'))

    movies = data_manager.get_movies(user_id)
    return render_template("movies.html", movies=movies, user_id=user_id, user_name=user.name)


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """
    Add a new movie to a user's favorites by fetching info from OMDb API.
    """
    user = User.query.get(user_id)
    if not user:
        flash("User not found!", "error")
        return redirect(url_for('index'))

    title = request.form['title'].strip()
    if not title:
        flash("Please enter a movie title.", "error")
        return redirect(url_for('list_movies', user_id=user_id))

    # OMDb API
    response = requests.get(
        "http://www.omdbapi.com/",
        params={"t": title, "apikey": OMDB_API_KEY}
    )
    data = response.json()
    if data.get("Response") != "True":
        flash(f"Movie '{title}' not found in OMDb.", "error")
        return redirect(url_for('list_movies', user_id=user_id))

    movie = Movie(
        name=data["Title"],
        director=data.get("Director", "Unknown"),
        year=data.get("Year", "Unknown"),
        poster_url=data.get("Poster", ""),
        user_id=user_id
    )
    data_manager.add_movie(movie)
    flash(f"Movie '{title}' added to {user.name}'s favorites.", "success")
    return redirect(url_for('list_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    """
    Update the title of a specific movie.
    """
    user = User.query.get(user_id)
    if not user:
        flash("User not found!", "error")
        return redirect(url_for('index'))

    new_title = request.form['new_title'].strip()
    if not new_title:
        flash("New title cannot be empty.", "error")
        return redirect(url_for('list_movies', user_id=user_id))

    data_manager.update_movie(movie_id, new_title)
    flash("Movie updated successfully.", "success")
    return redirect(url_for('list_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    """
    Delete a movie from a user's favorites.
    """
    user = User.query.get(user_id)
    if not user:
        flash("User not found!", "error")
        return redirect(url_for('index'))

    data_manager.delete_movie(movie_id)
    flash("Movie deleted successfully.", "success")
    return redirect(url_for('list_movies', user_id=user_id))


# Error handling

@app.errorhandler(404)
def page_not_found(e):
    """
    Handle 404 Not Found errors.
    """
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """
    Handle 500 Internal Server errors.
    """
    return render_template('500.html'), 500


# Run the app
if __name__ == "__main__":
    """
    Runs the Flask development server in debug mode.
    """
    app.run(debug=True)
