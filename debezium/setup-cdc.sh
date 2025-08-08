#!/bin/bash

echo "🚀 Setting up Debezium CDC for Chat Database"
echo "============================================="

# Wait for Kafka Connect to be ready
echo "⏳ Waiting for Kafka Connect to be ready..."
until curl -f http://localhost:8083/; do
  echo "Kafka Connect is not ready yet. Waiting 5 seconds..."
  sleep 5
done

echo "✅ Kafka Connect is ready!"

# Create the PostgreSQL connector
echo "📡 Creating PostgreSQL Debezium connector..."
curl -X POST -H "Content-Type: application/json" \
  --data @debezium/postgres-connector.json \
  http://localhost:8083/connectors

echo ""
echo "🔍 Checking connector status..."
curl -s http://localhost:8083/connectors/chat-postgres-connector/status | jq '.'

echo ""
echo "📋 Available connectors:"
curl -s http://localhost:8083/connectors | jq '.'

echo ""
echo "🎉 Debezium setup complete!"
echo ""
echo "📚 CDC Topics created:"
echo "  - chat.cdc.messages"
echo "  - chat.cdc.conversations" 
echo "  - chat.cdc.conversation_members"
echo "  - chat.cdc.message_deliveries"
echo ""
echo "🔧 Monitor with:"
echo "  - Connector status: curl http://localhost:8083/connectors/chat-postgres-connector/status"
echo "  - Kafka topics: docker exec web2-chat-app-kafka-1 kafka-topics --bootstrap-server localhost:9092 --list"
