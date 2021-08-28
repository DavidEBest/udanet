from kafka import KafkaProducer
import json

TOPIC_NAME = 'location'
KAFKA_SERVER = 'localhost:9092'

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    api_version=(2,8,0),
    value_serializer=lambda v: json.dumps(v).encode('utf-8'))

producer.send(
    TOPIC_NAME,
    {
        "person_id": 10,
        "creation_time": "2020-07-07T10:37:06",
        "latitude": "-122.290883",
        "longitude": "37.55363"
    })
# producer.send(TOPIC_NAME, b'Test Message!!!')
producer.flush()