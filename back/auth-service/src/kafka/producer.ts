import { Kafka } from 'kafkajs';
import { config } from 'dotenv';
config();

const brokers = process.env.KAFKA_BOOTSTRAP_SERVERS ? process.env.KAFKA_BOOTSTRAP_SERVERS.split(',') : ['localhost:9092'];
const kafka = new Kafka({
  clientId: 'auth-service',
  brokers,
});

export const kafkaProducer = kafka.producer();

export async function connectKafkaProducer() {
  await kafkaProducer.connect();
}

export async function sendUserCreatedEvent(user: any) {
  await kafkaProducer.send({
    topic: 'user.created',
    messages: [
      { value: JSON.stringify(user) }
    ],
  });
}
