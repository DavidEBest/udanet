import grpc

import sys
import os 

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import location_pb2
import location_pb2_grpc

"""
Sample implementation of a writer that can be used to write messages to gRPC.
"""

print("Sending sample payload...")

channel = grpc.insecure_channel("localhost:30005")
stub = location_pb2_grpc.LocationServiceStub(channel)

# Update this with desired payload
loc = location_pb2.LocationMessage(
    person_id=1,
    creation_time='2021-08-18 10:37:06',
    latitude='39.758949',
    longitude='-84.191605'
)

response = stub.Create(loc)
print("1", response)

location_id = location_pb2.LocationIdMessage(id=29)
response_2 = stub.Get(location_id)
print("2", response_2)

search = location_pb2.LocationSearchParams(
    person_id=5,
    start_date='2020-01-01 10:37:06',
    end_date='2021-09-18 10:37:06',
    meters=10
)
response_3 = stub.Search(search)
print("3", response_3)