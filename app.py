import os
from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from db import db
import models
from blocklist import is_in_blocklist

from models.user import UserModel
from resources.item import blp as ItemBlueprint
from resources.store import blp as StoreBlueprint
from resources.tags import blp as TagBlueprint
from resources.user import blp as UserBlueprint

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

def create_app(db_url=None):
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "jose"  # Make sure to use a secure key in production
    
    db.init_app(app)
    migrate = Migrate(app, db)
    api = Api(app)
    jwt = JWTManager(app)

    with app.app_context():
        print("Creating database tables...")
#        db.create_all() # This is not needed when using Flask-Migrate
        print("Database tables created!")

#    @jwt.additional_claims_loader
#    def add_claims_to_jwt(identity):
#        if UserBlueprint.get_user_by_id(identity).admin:
#            return {"is_admin": True}
#        return {"is_admin": False}

    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        user = UserModel.query.get(identity)
        if user and user.admin:
            return {"is_admin": True}
        return {"is_admin": False}

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return is_in_blocklist(jwt_payload["jti"])

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "The token has expired.", "error": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "Signature verification failed.", "error": "invalid_token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "description": "Request does not contain an access token.",
            "error": "authorization_required"
        }), 401

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return jsonify({
            "description": "The token is not fresh.",
            "error": "fresh_token_required"
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "description": "The token has been revoked.",
            "error": "token_revoked"
        }), 401

    api.register_blueprint(ItemBlueprint)
    api.register_blueprint(StoreBlueprint)
    api.register_blueprint(TagBlueprint)
    api.register_blueprint(UserBlueprint)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run()
else:
    app = create_app()
