from flask import Flask, jsonify, request, abort
app = Flask(__name__)

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

app.config["JWT_SECRET_KEY"] = "Tomato" 
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
jwt = JWTManager(app)

from datetime import timedelta
from flask_marshmallow import Marshmallow
from marshmallow.validate import Length
ma = Marshmallow(app)


## DB CONNECTION AREA

from flask_sqlalchemy import SQLAlchemy 
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://tomato:123456@localhost:5432/ripe_tomatoes_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# CLI COMMANDS AREA

@app.cli.command("create")
def create_db():
    db.create_all()
    print("Tables created")

@app.cli.command("seed")
def seed_db():

    movie1 = Movie(
        title = "Spider-Man: No Way Home",
        genre = "Action",
        length = 148,
        year = 2021
    )
    db.session.add(movie1)

    movie2 = Movie(
        title = "Dune",
        genre = "Sci-fi",
        length = 155,
        year = 2021
    )
    db.session.add(movie2)

    actor1 = Actor(
        first_name = "Tom",
        last_name = "Holland",
        gender = "male",
        country = "UK"
    )
    db.session.add(actor1)

    actor2 = Actor(
        first_name = "Marisa",
        last_name = "Tomei",
        gender = "female",
        country = "USA"
    )
    db.session.add(actor2)

    actor3 = Actor(
        first_name = "Timothee",
        last_name = "Chalemet",
        gender = "male",
        country = "USA"
    )
    db.session.add(actor3)

    actor4 = Actor(
        first_name = "Zendaya",
        last_name = "",
        gender = "female",
        country = "USA"
    )
    db.session.add(actor4)

    user = User(
        username = "tomato",
        password = bcrypt.generate_password_hash("password123").decode("utf-8")
    )
    db.session.add(user)
   
    db.session.commit()
    print("Tables seeded") 

@app.cli.command("drop")
def drop_db():
    db.drop_all()
    print("Tables dropped") 

# MODELS AREA

class Movie(db.Model):
    __tablename__= "MOVIES"
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String())
    genre = db.Column(db.String())
    length = db.Column(db.Integer())
    year = db.Column(db.Integer())

class Actor(db.Model):
    __tablename__= "ACTORS"
    id = db.Column(db.Integer,primary_key=True)  
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    gender = db.Column(db.String())
    country = db.Column(db.String())

class User(db.Model):
    __tablename__ = "USERS"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)

# SCHEMAS AREA

class MovieSchema(ma.Schema):
    class Meta:
        fields = ("id", "title", "genre", "length", "year")

movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)

class ActorSchema(ma.Schema):
    class Meta:
        fields = ("id", "first_name", "last_name", "gender", "country")

actor_schema = ActorSchema()
actors_schema = ActorSchema(many=True)

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
    password = ma.String(validate=Length(min=8))

user_schema = UserSchema()
users_schema = UserSchema(many=True)

# ROUTING AREA

@app.route("/")
def hello():
  return "Welcome to Ripe Tomatoes API"

@app.route("/movies", methods=["GET"])
def get_movies():
    movies_list = Movie.query.all()
    result = movies_schema.dump(movies_list)
    return jsonify(result)

@app.route("/movies", methods=["POST"])
@jwt_required()
def movie_create():
    movie_fields = movie_schema.load(request.json)

    new_movie = Movie()
    new_movie.title = movie_fields["title"]
    new_movie.genre = movie_fields["genre"]
    new_movie.length = movie_fields["length"]
    new_movie.year = movie_fields["year"]

    db.session.add(new_movie)
    db.session.commit()
    
    return jsonify(movie_schema.dump(new_movie))

@app.route("/movies/<int:id>", methods=["DELETE"])
@jwt_required()
def movie_delete(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return abort(401, description="Invalid user")
        
    movie = Movie.query.filter_by(id=id).first()
    
    if not Movie:
        return abort(400, description= "Movie not found in the database")

    db.session.delete(movie)
    db.session.commit()
    
    return jsonify(movie_schema.dump(movie))

@app.route("/actors", methods=["GET"])
def get_actors():
    actors_list = Actor.query.all()
    result = actors_schema.dump(actors_list)
    return jsonify(result)

@app.route("/actors", methods=["POST"])
@jwt_required()
def actor_create():
    actor_fields = actor_schema.load(request.json)

    new_actor = Actor()
    new_actor.first_name = actor_fields["first_name"]
    new_actor.last_name = actor_fields["last_name"]
    new_actor.country = actor_fields["country"]
    new_actor.gender = actor_fields["gender"]

    db.session.add(new_actor)
    db.session.commit()
    
    return jsonify(actor_schema.dump(new_actor))

@app.route("/actors/<int:id>", methods=["DELETE"])
@jwt_required()
def actor_delete(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return abort(401, description="Invalid user")
        
    actor = Actor.query.filter_by(id=id).first()
    
    if not Actor:
        return abort(400, description= "Actor not found in the db")

    db.session.delete(actor)
    db.session.commit()
    
    return jsonify(actor_schema.dump(actor))

## AUTH ROUTES

@app.route("/auth/signup", methods=["POST"])
def auth_signup():
    user_fields = user_schema.load(request.json)
    user = User.query.filter_by(username=user_fields["username"]).first()

    if user:
        return abort(400, description="Username already registered")
        
    user = User()
    user.username = user_fields["username"]
    user.password = bcrypt.generate_password_hash(user_fields["password"]).decode("utf-8")

    db.session.add(user)
    db.session.commit()

    expiry = timedelta(days=1)
    access_token = create_access_token(identity=str(user.id), expires_delta=expiry)
    
    return jsonify({"token": access_token })

@app.route("/auth/signin", methods=["POST"])
def auth_sigin():
    user_fields = user_schema.load(request.json)
    
    user = User.query.filter_by(username=user_fields["username"]).first()
    # there is not a user with that email or if the password is no correct send an error
    if not user or not bcrypt.check_password_hash(user.password, user_fields["password"]):
        return abort(401, description="Incorrect username and password")
    
    expiry = timedelta(days=1)
    access_token = create_access_token(identity=str(user.id), expires_delta=expiry)

    return jsonify({"token": access_token })

