from src.constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT
from flask import Blueprint, app, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import validators
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from flasgger import swag_from
from src.database import User, db
#Blueprint for users' authentication
auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


#Tell a user that his data got submitted succesfully
@auth.post('/register')
@swag_from('./docs/auth/register.yaml')
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    

    if len(password) < 6:
        return jsonify({'error': "Please, you entered a minimum of six charatrs"}), HTTP_400_BAD_REQUEST

    if len(username)<3:
        return jsonify({'error': "username is too short"}), HTTP_400_BAD_REQUEST
 
    if not username.isalnum() or " " in username:
        return jsonify({'error': "Must be alphanumeric with no spaces"}), HTTP_400_BAD_REQUEST
    
    if not validators.email(email):
        return jsonify({'error': "Email is not valid"}), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': "The email exists"}), HTTP_409_CONFLICT

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({'error': "The username exists"}), HTTP_409_CONFLICT

    pwd_hash=generate_password_hash(password)

    user=User(username=username, password=pwd_hash, email=email)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': "User created",
        'user': {
            'username': username, "email": email
        }
    }), HTTP_201_CREATED


    return jsonify({"User Created"})

#Get the current loged in user

@auth.post('/login')
@swag_from('./docs/auth/login.yaml')
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    user = User.query.filter_by(email=email).first()

    if user:
        is_pass_correct = check_password_hash(user.password, password)

        if is_pass_correct:
            refresh = create_refresh_token(identity=user.id)
            access = create_access_token(identity=user.id)

            return jsonify({
                'user': {
                    'refresh': refresh,
                    'access': access,
                    'username': user.username,
                    'email': user.email
                }
            }), HTTP_201_CREATED

    return jsonify({'error':'Wrong credentials'}), HTTP_401_UNAUTHORIZED

@auth.get("/me")
#jwt_required decorator is used to protect routes or endpoints in my Flask application, 
# ensuring that only authenticated users with valid JWTs can access them
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        'username': user.username,
        'email': user.email
    }), HTTP_200_OK


@auth.post('/token/refresh')
#Refreshing the access token
@jwt_required(refresh=True)
def refresh_users_token():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)

    return jsonify({
        'access': access
    }), HTTP_200_OK