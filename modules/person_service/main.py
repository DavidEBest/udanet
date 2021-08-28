import time
from concurrent import futures

import grpc
import person_pb2
import person_pb2_grpc
from models import session, Person
import config

class PersonServicer(person_pb2_grpc.PersonServiceServicer):
    def Create(self, request, context):

        new_person = Person()
        new_person.first_name = request.first_name
        new_person.last_name = request.last_name
        new_person.company_name = request.company_name

        session.add(new_person)
        session.commit()

        request_value = {
            "id": new_person.id,
            "first_name": new_person.first_name,
            "last_name": new_person.last_name,
            "company_name": new_person.company_name,
        }
        # print(request_value)

        return person_pb2.PersonMessage(**request_value)

    def Get(self, request, context):

        person_id = request.id
        person = session.query(Person).get(person_id)

        request_value = {
            "id": person.id,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "company_name": person.company_name,
        }
        # print(request_value)

        return person_pb2.PersonMessage(**request_value)

    def List(self, request, context):
        people = session.query(Person).all()

        result = person_pb2.PersonMessageList()
        for person in people:
            request_value = {
                "id": person.id,
                "first_name": person.first_name,
                "last_name": person.last_name,
                "company_name": person.company_name,
            }
            result.people.extend([person_pb2.PersonMessage(**request_value)])
            # print(person)
        return result


# Initialize gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
person_pb2_grpc.add_PersonServiceServicer_to_server(PersonServicer(), server)

print("Server starting on port" + config.SERVICE_PORT)
server.add_insecure_port("[::]:" + config.SERVICE_PORT)
server.start()
# Keep thread alive
try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    server.stop(0)