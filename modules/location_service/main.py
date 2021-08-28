import time
from concurrent import futures
from datetime import datetime, timedelta
from typing import List

import grpc
import location_pb2
import location_pb2_grpc
from models import session, Location
from sqlalchemy.sql import text
from geoalchemy2.functions import ST_Point
import config

class LocationServicer(location_pb2_grpc.LocationServiceServicer):
    def Create(self, request, context):
        new_location = Location()
        new_location.person_id = request.person_id
        new_location.creation_time = request.creation_time
        new_location.coordinate = ST_Point(request.latitude, request.longitude)

        session.add(new_location)
        session.commit()

        request_value = {
            "id": new_location.id,
            "person_id": new_location.person_id,
            "creation_time": str(new_location.creation_time),
            "latitude": new_location.latitude,
            "longitude": new_location.longitude,
        }

        return location_pb2.LocationMessage(**request_value)

    def Get(self, request, context):

        location_id = request.id
        location = session.query(Location).get(location_id)

        request_value = {
            "id": location.id,
            "person_id": location.person_id,
            "creation_time": str(location.creation_time),
            "latitude": location.latitude,
            "longitude": location.longitude,
        }
        # print(request_value)

        return location_pb2.LocationMessage(**request_value)

    def Search(self, request, context):
        person_id = request.person_id
        start_date = datetime.strptime(request.start_date, '%Y-%m-%d %H:%M:%S.%f')
        end_date = datetime.strptime(request.end_date, '%Y-%m-%d %H:%M:%S.%f')
        meters = request.meters

        locations: List = session.query(Location).filter(
            Location.person_id == person_id
        ).filter(Location.creation_time < end_date).filter(
            Location.creation_time >= start_date
        ).all()

        data = []
        for location in locations:
            data.append(
                {
                    "person_id": person_id,
                    "longitude": location.longitude,
                    "latitude": location.latitude,
                    "meters": meters,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": (end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                }
            )

        query = text(
            """
        SELECT  person_id, id, ST_X(coordinate), ST_Y(coordinate), creation_time
        FROM    location
        WHERE   ST_DWithin(coordinate::geography,ST_SetSRID(ST_MakePoint(:latitude,:longitude),4326)::geography, :meters)
        AND     person_id != :person_id
        AND     TO_DATE(:start_date, 'YYYY-MM-DD') <= creation_time
        AND     TO_DATE(:end_date, 'YYYY-MM-DD') > creation_time;
        """
        )

        result = location_pb2.LocationMessageList()
        for line in tuple(data):
            for (
                exposed_person_id,
                location_id,
                exposed_lat,
                exposed_long,
                exposed_time,
            ) in session.execute(query, line):
                request_value = {
                    "id": location_id,
                    "person_id": exposed_person_id,
                    "creation_time": str(exposed_time),
                    "latitude": str(exposed_lat),
                    "longitude": str(exposed_long) 
                }
                result.locations.extend([location_pb2.LocationMessage(**request_value)])
        return result


# Initialize gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
location_pb2_grpc.add_LocationServiceServicer_to_server(LocationServicer(), server)


print("Server starting on port" + config.SERVICE_PORT)
server.add_insecure_port("[::]:" + config.SERVICE_PORT)
server.start()
# Keep thread alive
try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    server.stop(0)