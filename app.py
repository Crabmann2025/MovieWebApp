from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Movie  # import Modell

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movieweb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()  # Erstellt die Tabellen, falls sie noch nicht existieren

@app.route('/')
def home():
    return "Willkommen bei MoviWeb!"

if __name__ == "__main__":
    app.run(debug=True)
