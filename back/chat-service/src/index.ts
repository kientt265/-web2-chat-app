import express from 'express';
import { Server } from 'socket.io';
import {producer, consumer } from './config/kafka';
import http from 'http';
import cors from 'cors';
import swaggerUi from 'swagger-ui-express';
import YAML from 'yamljs';
import { config } from 'dotenv';
import { PrismaClient } from '@prisma/client';
import chatRoutes from './routes/chatRoutes';
import { initKafka } from './services/kafkaService';
import { handleSocketConnection, connectBotSocket } from './sockets/socketHandler';
config();

const prisma = new PrismaClient();
const app = express();
const server = http.createServer(app);
const swaggerDocument = YAML.load('./swagger.yaml');
//cors for socket.io
export const  io = new Server(server, {
  path: "/socket.io/",
  cors: {
    origin: 'http://localhost:5173',
    methods: ['GET', 'POST'],
    credentials: true
  }
});
const port = process.env.CHAT_PORT || 3002;

connectBotSocket(io);

handleSocketConnection(io);



//cors for http://localhost:5173
app.use(cors({
  origin: 'http://localhost:5173',
  credentials: true
}));
app.use(express.json());
app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));
app.use('/', chatRoutes);
app.get('/run', (req, res) => {
  res.send('Chat Service is running');
});


server.listen(port, async () => {
    console.log('\n=== Chat Service Status ===');
    console.log(`[Server] 🚀 HTTP Server running on port ${port}`);
    console.log(`[Socket] 🔌 Socket.IO server initialized`);
    console.log(`[CORS] ✅ CORS configured for origin: http://localhost:5173`);
    
    try {
        await initKafka(io);
        console.log('[Service] ✅ Chat service fully initialized\n');
    } catch (error) {
        console.error('[Service] ❌ Failed to initialize Kafka:', error);
        process.exit(1);
    }
});

process.on('SIGTERM', async () => {
    console.log('\n=== Shutting down Chat Service ===');
    console.log('[Service] 🛑 Received SIGTERM signal');
    
    try {
        await producer.disconnect();
        console.log('[Kafka] ✅ Producer disconnected');
        
        await consumer.disconnect();
        console.log('[Kafka] ✅ Consumer disconnected');
        
        await prisma.$disconnect();
        console.log('[Database] ✅ Database connection closed');
        
        server.close(() => {
            console.log('[Server] ✅ HTTP Server closed');
            console.log('[Service] 👋 Goodbye!\n');
            process.exit(0);
        });
    } catch (error) {
        console.error('[Service] ❌ Error during shutdown:', error);
        process.exit(1);
    }
});