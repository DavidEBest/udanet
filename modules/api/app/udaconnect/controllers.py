from datetime import datetime

from app.udaconnect.models import Connection, Location, Person
from app.udaconnect.schemas import (
    ConnectionSchema,
    LocationSchema,
    PersonSchema,
)
from app.udaconnect.services import ConnectionService, LocationService
from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from typing import Optional, List

import grpc
import app.udaconnect.grpc_defs.person_pb2 as person_pb2
import app.udaconnect.grpc_defs.person_pb2_grpc as person_pb2_grpc
import app.udaconnect.grpc_defs.location_pb2 as location_pb2
import app.udaconnect.grpc_defs.location_pb2_grpc as location_pb2_grpc
import config

DATE_FORMAT = "%Y-%m-%d"

api = Namespace("UdaConnect", description="Connections via geolocation.")  # noqa


# TODO: This needs better exception handling


@api.route("/locations")
class LocationsResource(Resource):
    @accepts(
        dict(name="person_id", type=int),
        dict(name="creation_time", type=str),
        dict(name="latitude", type=str),
        dict(name="longitude", type=str),
        api=api)
    @responds(schema=LocationSchema)
    def post(self) -> Location:
        payload = request.parsed_args

        channel = grpc.insecure_channel(config.LOCATION_HOST + ":" + config.LOCATION_PORT)
        stub = location_pb2_grpc.LocationServiceStub(channel)
        location = location_pb2.LocationMessage(
            id=payload['id'],
            person_id=payload['person_id'],
            creation_time=payload['creation_time'],
            latitude=payload['latitude'],
            longitude=payload['longitude']
        )
        response = stub.Create(location)
        return response


@api.route("/locations/<location_id>")
@api.param("location_id", "Unique ID for a given Location", _in="query")
class LocationResource(Resource):
    @responds(schema=LocationSchema)
    def get(self, location_id) -> Location:
        channel = grpc.insecure_channel(config.LOCATION_HOST + ":" + config.LOCATION_PORT)
        stub = location_pb2_grpc.LocationServiceStub(channel)
        location_id_msg = location_pb2.LocationIdMessage(id=int(location_id))
        response = stub.Get(location_id_msg)
        return response



@api.route("/persons")
class PersonsResource(Resource):
    @accepts(
        dict(name="first_name", type=str),
        dict(name="last_name", type=str),
        dict(name="company_name", type=str),
        api=api)
    @responds(schema=PersonSchema)
    def post(self) -> Person:
        payload = request.parsed_args

        channel = grpc.insecure_channel(config.PERSON_HOST + ":" + config.PERSON_PORT)
        stub = person_pb2_grpc.PersonServiceStub(channel)
        person = person_pb2.PersonMessage(
            first_name=payload['first_name'],
            last_name=payload['last_name'],
            company_name=payload['company_name']
        )
        response = stub.Create(person)
        return response

    @responds(schema=PersonSchema, many=True)
    def get(self) -> List[Person]:
        channel = grpc.insecure_channel(config.PERSON_HOST + ":" + config.PERSON_PORT)
        stub = person_pb2_grpc.PersonServiceStub(channel)
        response = stub.List(person_pb2.Empty())
        people = []
        for person in response.people:
            people.append({
                "id": person.id,
                "first_name": person.first_name,
                "last_name": person.last_name,
                "company_name": person.company_name
            })
        return people


@api.route("/persons/<person_id>")
@api.param("person_id", "Unique ID for a given Person", _in="query")
class PersonResource(Resource):
    @responds(schema=PersonSchema)
    def get(self, person_id) -> Person:
        channel = grpc.insecure_channel(config.PERSON_HOST + ":" + config.PERSON_PORT)
        stub = person_pb2_grpc.PersonServiceStub(channel)
        person_id_msg = person_pb2.PersonIdMessage(id=int(person_id))
        response = stub.Get(person_id_msg)
        return response


@api.route("/persons/<person_id>/connection")
@api.param("start_date", "Lower bound of date range", _in="query")
@api.param("end_date", "Upper bound of date range", _in="query")
@api.param("distance", "Proximity to a given user in meters", _in="query")
class ConnectionDataResource(Resource):
    @responds(schema=ConnectionSchema, many=True)
    def get(self, person_id) -> ConnectionSchema:
        start_date: datetime = datetime.strptime(
            request.args["start_date"], DATE_FORMAT
        )
        end_date: datetime = datetime.strptime(request.args["end_date"], DATE_FORMAT)
        distance: Optional[int] = request.args.get("distance", 5)

        results = ConnectionService.find_contacts(
            person_id=person_id,
            start_date=start_date,
            end_date=end_date,
            meters=distance,
        )
        return results
