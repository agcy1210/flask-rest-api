from flask import Flask,request, Response
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token,JWTManager,jwt_required, get_jwt_identity
from database.db import initialize_db
from database.models import Movie, User
import datetime


app = Flask(__name__)
app.config.from_envvar('ENV_FILE_LOCATION')
#export ENV_FILE_LOCATION=./.env -> run in cmd

bcrypt = Bcrypt(app)
jwt = JWTManager(app)

app.config['MONGODB_SETTINGS']= {
    'host': 'mongodb://localhost/movie-bag'
}

initialize_db(app)


@app.route('/api/movies')
def get_movies():
    movies = Movie.objects().to_json()
    return Response(movies, mimetype="application/json", status=200)

@app.route('/api/movies/<id>')
def get_movie(id):
    movies = Movie.objects.get(id=id).to_json()
    return Response(movies,mimetype="application/json", status=200)


@app.route('/api/movies', methods=['POST'])
@jwt_required()
def add_movie():
    user_id = get_jwt_identity()
    body = request.get_json()
    user = User.objects.get(id=user_id)
    movie = Movie(**body, added_by=user)
    movie.save()
    user.update(push__movies=movie)
    user.save()
    id = movie.id
    return {'id': str(id)}, 200


@app.route('/api/movies/<id>', methods=['PUT'])
@jwt_required()
def update_movie(id):
    user_id = get_jwt_identity()
    movie = Movie.objects.get(id=id, added_by=user_id)
    body = request.get_json()
    Movie.objects.get(id=id).update(**body)

    return '', 200


@app.route('/api/movies/<id>', methods=['DELETE'])
@jwt_required()
def delete_movie(id):
    user_id = get_jwt_identity()
    movie = Movie.objects.get(id=id, added_by=user_id)
    movie.delete()
    # Movie.objects.get(id=id).delete()
    return '', 200


@app.route('/api/auth/signup', methods=['POST'])
def signup():
    body = request.get_json()
    user = User(**body)
    user.hash_password()
    user.save()
    id = user.id
    return {'id': str(id)}, 200


@app.route('/api/auth/login', methods=['POST'])
def login():
    body = request.get_json()
    user = User.objects.get(email=body.get('email'))
    authorized = user.check_password(body.get('password'))

    if not authorized:
        return {'error': 'Email id or password invalid'}, 401

    expires = datetime.timedelta(days=7)
    access_token = create_access_token(identity=str(user.id), expires_delta=expires)

    return {'token':access_token}, 200



@app.route('/api/auth/users')
def get_users():
    users = User.objects().to_json()
    return Response(users, mimetype="application/json", status=200)


app.run()


