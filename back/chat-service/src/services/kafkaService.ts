import {producer, consumer } from '../config/kafka';
import {Server} from 'socket.io';
import { PrismaClient } from '@prisma/client';


const prisma = new PrismaClient();
export async function initKafka(io: Server) {
    try {
        await producer.connect();
        console.log('[Kafka] ✅ Producer connected successfully');
        
        await consumer.connect();
        console.log('[Kafka] ✅ Consumer connected successfully');
        
        await consumer.subscribe({ topic: 'private-chat-messages', fromBeginning: true });
        console.log('[Kafka] 📥 Subscribed to private-chat-messages topic');
        
        await consumer.subscribe({topic: 'group-chat-messages', fromBeginning: true});
        console.log('[Kafka] 📥 Subscribed to group-chat-messages topic');

        await consumer.run({
            eachMessage: async ({topic, partition, message}) => {
                try {
                    const msg = JSON.parse(message.value?.toString() || '{}');
                    console.log(`[Kafka] 📨 Received message on topic "${topic}":`, {
                        conversation_id: msg.conversation_id,
                        sender_id: msg.sender_id,
                        receiver: msg.receiver,
                        timestamp: new Date(msg.sent_at).toISOString()
                    });

                    io.to(msg.conversation_id).emit('new_message', msg);
                    console.log(`[Socket] 📤 Emitted message to room ${msg.conversation_id}`);

                    await prisma.messages.create({
                        data: {
                            message_id: msg.message_id,
                            conversation_id: msg.conversation_id,
                            sender_id: msg.sender_id,
                            content: msg.content,
                            sent_at: new Date(msg.sent_at),
                            is_read: false,
                        },
                    });
                    const sender = msg.sender_id;
                    msg.receiver.map((re: any) => {
                        (re.user_id !== sender) ? 
                        io.to(re.user_id).emit('new_msg_socker_user_personal', msg) :
                        re
                    })
                    console.log(`[Database] ✅ Message saved to database`);
                } catch (error) {
                    console.error('[Kafka] ❌ Error processing message:', error);
                }
            }
        });
    } catch (error) {
        console.error('[Kafka] ❌ Error initializing Kafka:', error);
        throw error;
    }
}