from flask import Flask, request, redirect, url_for, render_template
from models import db, Movie, User
from data_manager import DataManager
import requests
from dotenv import load_dotenv
import os


# Load OMDb API Key from .env
load_dotenv()  # Reads the .env file
OMDB_API_KEY = os.getenv("OMDB_API_KEY")


# Flask App & Database Setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moviweb.db'  # SQLite Database
db.init_app(app)  # Connect Flask with the database

data_manager = DataManager()

# Create the database tables at startup
with app.app_context():
    db.create_all()



# Routes

@app.route('/')
def index():
    """
    Home page route.
    Displays a list of all registered users.
    """
    users = data_manager.get_users()
    return render_template("index.html", users=users)


@app.route('/users', methods=['POST'])
def add_user():
    """
    Adds a new user to the database.
    Gets the 'name' from the submitted form and saves it.
    """
    name = request.form['name']
    data_manager.create_user(name)
    return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def list_movies(user_id):
    """
    Displays all movies for a specific user.

    Args:
        user_id (int): The ID of the user whose movies will be listed.
    """
    movies = data_manager.get_movies(user_id)
    return render_template("movies.html", movies=movies, user_id=user_id)


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """
    Adds a new movie to the user's favorites.
    Fetches movie details from OMDb API using the provided title.

    Args:
        user_id (int): The ID of the user to add the movie to.
    """
    title = request.form['title']
    # OMDb API request
    response = requests.get("http://www.omdbapi.com/",
                            params={"t": title, "apikey": OMDB_API_KEY})
    data = response.json()
    if data.get("Response") == "True":
        movie = Movie(
            name=data["Title"],
            director=data.get("Director", "Unknown"),
            year=data.get("Year", "Unknown"),
            poster_url=data.get("Poster", ""),
            user_id=user_id
        )
        data_manager.add_movie(movie)
    return redirect(url_for('list_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    """
    Updates the title of a specific movie in the user's favorites.

    Args:
        user_id (int): The ID of the user.
        movie_id (int): The ID of the movie to update.
    """
    new_title = request.form['new_title']
    data_manager.update_movie(movie_id, new_title)
    return redirect(url_for('list_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    """
    Deletes a specific movie from the user's favorite movies list.

    Args:
        user_id (int): The ID of the user.
        movie_id (int): The ID of the movie to delete.
    """
    data_manager.delete_movie(movie_id)
    return redirect(url_for('list_movies', user_id=user_id))



# Run the app
if __name__ == "__main__":
    """
    Runs the Flask development server in debug mode.
    """
    app.run(debug=True)
