import logging
from datetime import datetime, timedelta
from typing import Dict, List

from app import db
from app.udaconnect.models import Connection, Location, Person
from app.udaconnect.schemas import ConnectionSchema, LocationSchema, PersonSchema
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text

import grpc
import app.udaconnect.grpc_defs.person_pb2_grpc as person_pb2_grpc
import app.udaconnect.grpc_defs.person_pb2 as person_pb2
import app.udaconnect.grpc_defs.location_pb2 as location_pb2
import app.udaconnect.grpc_defs.location_pb2_grpc as location_pb2_grpc
import config


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-api")


class ConnectionService:
    @staticmethod
    def find_contacts(person_id: int, start_date: datetime, end_date: datetime, meters=5
    ) -> List[Connection]:
        """
        Finds all Person who have been within a given distance of a given Person within a date range.

        This will run rather quickly locally, but this is an expensive method and will take a bit of time to run on
        large datasets. This is by design: what are some ways or techniques to help make this data integrate more
        smoothly for a better user experience for API consumers?
        """
        # Cache all users in memory for quick lookup
        person_channel = grpc.insecure_channel(config.PERSON_HOST + ":" + config.PERSON_PORT)
        person_stub = person_pb2_grpc.PersonServiceStub(person_channel)
        response = person_stub.List(person_pb2.Empty())
        person_map: Dict[str, person_pb2.PersonMessage] = {person.id: person for person in response.people}

        location_channel = grpc.insecure_channel(config.LOCATION_HOST + ":" + config.LOCATION_PORT)
        location_stub = location_pb2_grpc.LocationServiceStub(location_channel)
        location_params = location_pb2.LocationSearchParams(
            person_id=person_id,
            start_date=str(start_date),
            end_date=str(end_date),
            meters=meters
        )
        locations = location_stub.Search(location_params)
        print(locations)

        result: List[Connection] = []
        for location in locations.locations:
            temp_person = person_map[location.person_id]
            result.append(
                Connection(
                    person=Person(
                        id=temp_person.id,
                        first_name=temp_person.first_name,
                        last_name=temp_person.last_name,
                        company_name=temp_person.company_name
                    ), location=Location(
                        id=location.id,
                        person_id=location.person_id,
                        latitude=location.latitude,
                        longitude=location.longitude,
                        creation_time=str(location.creation_time)
                    )
                )
            )

        return result