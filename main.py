from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, Length, NumberRange
import requests
import os
'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''
class Base(DeclarativeBase):
    pass
db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["FLASK_KEY"]
Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)

class RatingForm(FlaskForm):
    new_rating = FloatField(u'New Rating', validators=[DataRequired(), NumberRange(min=0, max=10)])
    new_review  = StringField(u'New Review', validators=[DataRequired(), Length(min=3, max=100)])
    submit = SubmitField("Confirm")

class MovieForm(FlaskForm):
    title = StringField(u'Movie title', validators=[DataRequired(), Length(min=1, max=50)])
    submit = SubmitField("Confirm")

movie_key = os.environ["MOVIE_KEY"]
movie_search_url = 'https://api.themoviedb.org/3/search/movie'
movie_headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzN2U3MjQ1YWFkYzZlOTlmMWUzZjk3NTk4NjU4NjEzOSIsIm5iZiI6MTczMzUwNDI1Ni4yNTUsInN1YiI6IjY3NTMyZDAwOGFmNmQzZmViM2IwMTk5OCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.HfdkND-M6COeh5Y7z_TVS6tSpcZ0Q8bap7QHg-LmPLA',
}

# CREATE DB
class Movie(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(unique=True)
    year: Mapped[int] = mapped_column()
    description: Mapped[str] = mapped_column()
    rating: Mapped[float] = mapped_column()
    ranking: Mapped[int] = mapped_column()
    review: Mapped[str] = mapped_column()
    img_url: Mapped[str] = mapped_column()

# CREATE TABLE
# with app.app_context():
#     db.create_all()
#     if not db.session.execute(db.select(Movie).where(Movie.title == 'Avatar The Way of Water')).scalar():
#         movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
#         db.session.add(movie)
#         db.session.commit()

@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(desc(Movie.rating))).scalars()
    rank = 1
    for movie in movies:
        movie.ranking = rank
        db.session.commit()
        rank += 1
    movies = db.session.execute(db.select(Movie).order_by(Movie.ranking)).scalars()
    return render_template("index.html", movies=movies)

@app.route("/edit/<title>", methods=['GET', 'POST'])
def edit(title):
    form = RatingForm()
    movie = db.session.execute(db.select(Movie).where(Movie.title == title)).scalar()
    if form.validate_on_submit():
        movie.rating = request.form.get('new_rating')
        movie.review = request.form.get('new_review')
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=form)

@app.route('/delete/<title>')
def delete(title):
    movie = db.session.execute(db.select(Movie).where(Movie.title == title)).scalar()
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/add', methods=['GET', 'POST'])
def add():
    form = MovieForm()
    if form.validate_on_submit():
        new_title = request.form.get('title')
        movie_query = {
            'query': new_title,
            'adult': True,
        }
        response = requests.get(url=movie_search_url, headers=movie_headers, params=movie_query)
        response.raise_for_status()
        movies = response.json()
        print(movies['results'][0]['backdrop_path'])
        return render_template('select.html', movies=movies['results'])
    return render_template('add.html', form=form)

@app.route('/info/<movie_id>')
def info(movie_id):
    response = requests.get(url=f'https://api.themoviedb.org/3/movie/{movie_id}', headers=movie_headers)
    response.raise_for_status()
    add_movie = response.json()
    new_movie = Movie(
        title = add_movie['title'],
        year = add_movie['release_date'][:4],
        description = add_movie['overview'],
        img_url = f"https://image.tmdb.org/t/p/w780{add_movie['backdrop_path']}",
        rating = 0,
        review = '',
        ranking = 0,
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', title=add_movie['title']))

if __name__ == '__main__':
    app.run(debug=True)
