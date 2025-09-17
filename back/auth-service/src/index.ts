import express from 'express';
import { config } from 'dotenv';
import cors from 'cors';
import { PrismaClient } from '@prisma/client';
import authRoutes from './routes/authRoutes';
import { connectKafkaProducer } from './kafka/producer';

config();

const prisma = new PrismaClient();
const app = express();
const port = process.env.AUTH_PORT || 3001;

app.use(cors());
app.use(express.json());
app.use('/', authRoutes);
app.get('/run', (req, res) => {
  res.send('Auth Service is running');
});

app.listen(port, async () => {
  await connectKafkaProducer();
  console.log(`Auth Service is running on port ${port}`);
});

process.on('SIGTERM', async () => {
  console.log('Shutting down Auth Service...');
  await prisma.$disconnect();
  process.exit(0);
});