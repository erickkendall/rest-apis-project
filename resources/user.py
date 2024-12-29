from sqlite3 import IntegrityError
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
from blocklist import add_to_blocklist, is_in_blocklist

from db import db
from models import UserModel
from schemas import UserSchema

blp = Blueprint("Users", __name__, description="Operations on users")

@blp.route("/refresh")
class UserRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        jti = get_jwt()["jti"]
        # Calculate token expiry time
        expires = get_jwt()["exp"] - get_jwt()["iat"]
        add_to_blocklist(jti, expires)
        return {"access_token": new_token}, 200


@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=str(user.id), fresh=True)
            refresh_token = create_refresh_token(identity=str(user.id))
            return {"access_token": access_token, "refresh_token": refresh_token}, 200

        abort(401, message="Invalid username or password")


#@blp.route("/logout")
#class UserLogout(MethodView):
#    @jwt_required()
#    def post(self):
#        jti = get_jwt()["jti"]
#        BLOCKLIST.add(jti)
#        return {"message": "User logged out"}, 200

@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jwt = get_jwt()
        jti = jwt["jti"]
        # Calculate token expiry time
        expires = jwt["exp"] - jwt["iat"]
        add_to_blocklist(jti, expires)
        return {"message": "Successfully logged out"}, 200

@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel(**user_data)
        if UserModel.query.filter(UserModel.username == user.username).first():
            abort(409, message="User already exists")
        user = UserModel(
            username=user.username,
            password=pbkdf2_sha256.hash(user.password),
        )
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            abort(400, message="An error occurred while registering the user")

        return {"message": "User registered successfully"}, 201


@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted"}, 200


@blp.route("/users")
class Users(MethodView):
    @blp.response(200, UserSchema(many=True))
    def get(self):
        return UserModel.query.all()

    def delete(self):
        UserModel.query.delete()
        db.session.commit()
        return {"message": "All users deleted"}, 200
