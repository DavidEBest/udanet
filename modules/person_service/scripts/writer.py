import grpc

import sys
import os 

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import person_pb2
import person_pb2_grpc

"""
Sample implementation of a writer that can be used to write messages to gRPC.
"""

print("Sending sample payload...")

channel = grpc.insecure_channel("localhost:30005")
stub = person_pb2_grpc.PersonServiceStub(channel)

# Update this with desired payload
person = person_pb2.PersonMessage(
    first_name="Dave",
    last_name="Best",
    company_name="Mile Two",
)

response = stub.Create(person)
print("1", response)

person_id = person_pb2.PersonIdMessage(id=1)
response_2 = stub.Get(person_id)
print("2", response_2)

empty = person_pb2.Empty()
response_3 = stub.List(empty)
print("3", response_3)