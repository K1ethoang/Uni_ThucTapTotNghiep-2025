#!/bin/sh

# Kiểm tra xem Kafka Connect đã sẵn sàng chưa
while ! curl -s http://kafka-connect:8083/connectors; do
  echo "Kafka Connect is not ready yet. Retrying in 5 seconds..."
  sleep 5
done

echo "Registering MySQL Debezium Connector..."

envsubst < /register-mysql.json | curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" http://kafka-connect:8083/connectors/ -d @-

echo "Connector registered successfully!"