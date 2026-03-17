from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource

from model.titanic import TitanicModel


titanic_api = Blueprint("titanic_api", __name__, url_prefix="/api/titanic")
api = Api(titanic_api)


class _Predict(Resource):
    def post(self):
        passenger = request.get_json() or {}
        titanic_model = TitanicModel.get_instance()
        response = titanic_model.predict(passenger)
        return jsonify(response)


api.add_resource(_Predict, "/predict")
