from datetime import datetime
import config
from kafka import KafkaConsumer
import json
from models import session, Location
from geoalchemy2.functions import ST_Point


TOPIC_NAME = 'location'

server_name = config.KAFKA_HOST + ':' + config.KAFKA_PORT
print("server", server_name)
consumer = KafkaConsumer(
    TOPIC_NAME,
    bootstrap_servers=server_name,
    api_version=(2,8,0),
    value_deserializer=lambda m: json.loads(m.decode('ascii')))
for message in consumer:
    data = message.value
    print(data)
    new_location = Location()
    new_location.person_id = data['person_id']
    if data['creation_time'] == '':
        new_location.creation_time = datetime.now()
    else:
        new_location.creation_time = data['creation_time']
    new_location.coordinate = ST_Point(data['latitude'], data['longitude'])

    session.add(new_location)
    session.commit()
