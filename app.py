from flask import Flask, request, redirect, url_for, render_template, flash
from models import db, Movie, User
from data_manager import DataManager
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "fallbacksecret")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moviweb.db'
app.config['SECRET_KEY'] = SECRET_KEY
db.init_app(app)

data_manager = DataManager()

# Create database tables if they do not exist
with app.app_context():
    db.create_all()



# Routes


@app.route('/')
def index():
    """
    Home page: Display all users and any flash messages.
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
    return render_template(
        "movies.html",
        movies=movies,
        user_id=user_id,
        user_name=user.name
    )


@app.route('/users/<int:user_id>/movies/<int:movie_id>', methods=['GET'])
def movie_detail(user_id, movie_id):
    """
    Show details of a single movie (poster, title, plot, and actions).
    """
    user = User.query.get(user_id)
    if not user:
        flash("User not found!", "error")
        return redirect(url_for('index'))

    movie = Movie.query.get(movie_id)
    if not movie:
        flash("Movie not found!", "error")
        return redirect(url_for('list_movies', user_id=user_id))

    return render_template(
        "movie_detail.html",
        movie=movie,
        user_id=user_id,
        user_name=user.name
    )


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

    # OMDb API request
    try:
        response = requests.get(
            "http://www.omdbapi.com/",
            params={"t": title, "apikey": OMDB_API_KEY},
            timeout=5
        )
        data = response.json()
    except Exception:
        flash("Error connecting to OMDb API.", "error")
        return redirect(url_for('list_movies', user_id=user_id))

    if data.get("Response") != "True":
        flash(f"Movie '{title}' not found in OMDb.", "error")
        return redirect(url_for('list_movies', user_id=user_id))

    movie = Movie(
        name=data["Title"],
        director=data.get("Director", "Unknown"),
        year=data.get("Year", "Unknown"),
        poster_url=data.get("Poster", ""),
        actors=data.get("Actors", ""),
        plot=data.get("Plot", ""),
        user_id=user_id
    )
    data_manager.add_movie(movie)
    flash(f"Movie '{title}' added to {user.name}'s favorites.", "success")
    return redirect(url_for('list_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/rate', methods=['POST'])
def rate_movie(user_id, movie_id):
    """
    Save the rating (1–10 stars) of a movie for a specific user.
    """
    user = User.query.get(user_id)
    if not user:
        flash("User not found!", "error")
        return redirect(url_for('index'))

    movie = Movie.query.get(movie_id)
    if not movie:
        flash("Movie not found!", "error")
        return redirect(url_for('list_movies', user_id=user_id))

    rating = request.form.get('rating')
    if rating and rating.isdigit() and 1 <= int(rating) <= 10:
        data_manager.rate_movie(movie_id, int(rating))
        flash(f"Rating saved for '{movie.name}': {rating} stars.", "success")
    else:
        flash("Invalid rating. Please select between 1 and 10 stars.", "error")

    return redirect(url_for('movie_detail', user_id=user_id, movie_id=movie_id))



@app.route('/users/<int:user_id>/movies/<int:movie_id>/edit', methods=['GET', 'POST'])
def edit_movie(user_id, movie_id):
    """
    Edit a movie: GET shows the form, POST saves changes.
    """
    user = User.query.get(user_id)
    if not user:
        flash("User not found!", "error")
        return redirect(url_for('index'))

    movie = Movie.query.get(movie_id)
    if not movie:
        flash("Movie not found!", "error")
        return redirect(url_for('list_movies', user_id=user_id))

    if request.method == "POST":
        movie.name = request.form.get('name', movie.name)
        movie.director = request.form.get('director', movie.director)
        movie.actors = request.form.get('actors', movie.actors)
        movie.plot = request.form.get('plot', movie.plot)

        db.session.commit()
        flash("Movie updated successfully.", "success")
        return redirect(url_for('movie_detail', user_id=user_id, movie_id=movie_id))

    return render_template("movie_detail_edit.html", movie=movie, user_id=user_id, user_name=user.name)

@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    """
    Update multiple fields of a specific movie (title, director, actors, plot).
    """
    user = User.query.get(user_id)
    if not user:
        flash("User not found!", "error")
        return redirect(url_for('index'))

    movie = Movie.query.get(movie_id)
    if not movie:
        flash("Movie not found!", "error")
        return redirect(url_for('list_movies', user_id=user_id))

    # Get updated fields from form
    updates = {
        "name": request.form.get("name", "").strip(),
        "director": request.form.get("director", "").strip(),
        "actors": request.form.get("actors", "").strip(),
        "plot": request.form.get("plot", "").strip()
    }

    # Only save non-empty values
    for field, value in updates.items():
        if value:
            setattr(movie, field, value)

    db.session.commit()
    flash("Movie updated successfully.", "success")
    return redirect(url_for('movie_detail', user_id=user_id, movie_id=movie_id))


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
def page_not_found(error):
    """
    Handle 404 Not Found errors.
    """
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 Internal Server errors.
    """
    return render_template('500.html'), 500


if __name__ == "__main__":
    """
    Run the Flask development server in debug mode.
    """
    app.run(debug=False)
