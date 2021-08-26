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

DATE_FORMAT = "%Y-%m-%d"

api = Namespace("UdaConnect", description="Connections via geolocation.")  # noqa


# TODO: This needs better exception handling


@api.route("/locations")
@api.route("/locations/<location_id>")
@api.param("location_id", "Unique ID for a given Location", _in="query")
class LocationResource(Resource):
    @accepts(schema=LocationSchema)
    @responds(schema=LocationSchema)
    def post(self) -> Location:
        request.get_json()
        location: Location = LocationService.create(request.get_json())
        return location

    @responds(schema=LocationSchema)
    def get(self, location_id) -> Location:
        location: Location = LocationService.retrieve(location_id)
        return location


@api.route("/persons")
class PersonsResource(Resource):
    @accepts(schema=PersonSchema)
    @responds(schema=PersonSchema)
    def post(self) -> Person:
        payload = request.get_json()

        channel = grpc.insecure_channel("person_service:5000")
        stub = person_pb2_grpc.PersonServiceStub(channel)
        person = person_pb2.PersonMessage(
            first_name=payload.first_name,
            last_name=payload.last_name,
            company_name=payload.company_name
        )
        response = stub.Create(person)
        return response

    @responds(schema=PersonSchema, many=True)
    def get(self) -> List[Person]:
        channel = grpc.insecure_channel("person_service:5000")
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
        channel = grpc.insecure_channel("person_service:5000")
        stub = person_pb2_grpc.PersonServiceStub(channel)
        person_id_msg = person_pb2.PersonIdMessage(id=str(person_id))
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