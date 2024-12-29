from sqlite3 import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
import uuid
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from db import db
from models.store import StoreModel
from schemas import StoreSchema

blp = Blueprint('Stores', __name__, description='Operations on stores')


@blp.route("/store/<string:store_id>")
class Store(MethodView):
    @blp.response(200, StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store

    def delete(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": "Store deleted"}, 200


@blp.route("/store")
class StoresList(MethodView):
    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()

    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(
                400,
                message="A store with that name already exists."
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            abort(500, message="An error occurred while saving the store.")
        return store, 201
