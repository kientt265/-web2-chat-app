import { PrismaClient } from "@prisma/client";
import { producer } from '../config/kafka';
import { Server, Socket } from "socket.io";
import { randomUUID } from "crypto";
import { authSocket } from "../middleware/authSocket";
import { ResponeAI } from "../types/types";
import WebSocket from 'ws';

const prisma = new PrismaClient();
let botWs: WebSocket;

export const connectBotSocket = (io: Server) => {
    try {
        botWs = new WebSocket("ws://web2-chat-app-router-agent-1:3007/api/v1/ws");
        botWs.on('open', () => {
            console.log("✅ Connected to Router Agent WebSocket");
            botWs.send(JSON.stringify({
                type: "ping",
                data: {},
                message_id: "ping-1"
            }));
        });

        botWs.on('message', (msg: WebSocket.RawData) => {
            const message = JSON.parse(msg.toString()) as ResponeAI;
            console.log("📩 Received:", message);

            if (message.type === "response") {
                const botMessage = {
                    message_id: randomUUID(),
                    conversation_id: message.data.session_id,
                    sender_id: "00000000-0000-0000-0000-000000000001",
                    content: message.data.response,
                    sent_at: new Date().toISOString(),
                    is_read: false
                };

                io.to(message.data.session_id).emit('new_message', botMessage);

                prisma.messages.create({ data: botMessage })
                    .then(() => console.log(`[Bot] ✅ Bot reply saved to DB`))
                    .catch(err => console.error(`[Bot] ❌ Failed to save bot reply:`, err));
            }
        });

        botWs.on('close', () => {
            console.log("❌ Disconnected from Router Agent WebSocket");
        });

        botWs.on('error', (err) => {
            console.error("⚠️ WebSocket error:", err);
        });
    } catch (error) {
        console.error("[Bot] ❌ Failed to connect to Router Agent WebSocket:", error);
    }
}

export const handleSocketConnection = (io: Server) => {
    console.log("[Init] handleSocketConnection called");


    io.on('connection', (socket: Socket) => {
        console.log(`[Socket] ✨ New client connected | ID: ${socket.id}`);
        console.log(`[Socket] 🔑 Auth token:`, socket.handshake.auth);

        socket.on('join-app', (userId: string) => {
            try {
                socket.data.userId = userId;
                socket.join(userId);
                console.log(`[Socket] 👤 User ${userId} joined personal room`);
            } catch (error) {
                console.error(`[Socket] ❌ Error joining personal room:`, error);
                socket.emit('error', { message: 'Failed to join conversation' });
            }
        })

        socket.on('join_conversation', async (conversationId: string) => {
            try {
                const userId = socket.data.userId;
                socket.data.conversationId = conversationId;
                //const userId = socket.handshake.auth.token;
                console.log(`[Socket] 🚪 User ${socket.id} attempting to join conversation ${conversationId}`);
                socket.join(conversationId);
                console.log(`[Socket] ✅ User ${socket.id} joined conversation ${conversationId}`);
                socket.emit('join_success', { conversationId });
            } catch (error) {
                console.error(`[Socket] ❌ Error joining conversation:`, error);
                socket.emit('error', { message: 'Failed to join conversation' });
            }
        });

        socket.on('send_message', async (data: {
            conversation_id: string;
            sender_id: string;
            content: string
        }) => {
            console.log(`[Socket] 📩 Message received from client:`, data);
            try {

                if (!data.conversation_id || !data.sender_id || !data.content) {
                    console.error('[Socket] ❌ Missing required fields:', data);
                    throw new Error('Missing required fields');
                }

                if (!isValidUUID(data.conversation_id) || !isValidUUID(data.sender_id)) {
                    console.error('[Socket] ❌ Invalid UUID format:', {
                        conversation_id: data.conversation_id,
                        sender_id: data.sender_id
                    });
                    throw new Error('Invalid UUID format');
                }

                const isMember = await prisma.conversation_members.findFirst({
                    where: {
                        conversation_id: data.conversation_id,
                        user_id: data.sender_id
                    }
                });

                if (!isMember) {
                    console.warn(`[Socket] ⚠️ User ${data.sender_id} not authorized for conversation ${data.conversation_id}`);
                    throw new Error('Sender is not a member of this conversation');
                }

                const conversation = await prisma.conversations.findUnique({
                    where: { conversation_id: data.conversation_id },
                    select: { type: true },
                });

                if (!conversation) {
                    throw new Error('Conversation not found');
                }

                const members = await prisma.conversation_members.findMany({
                    where: {
                        conversation_id: data.conversation_id,
                    },
                });
                const receiver: string[] = [];
                members.map((mem) => {
                    receiver.push(mem.user_id);
                })
                const message = {
                    message_id: randomUUID(),
                    ...data,
                    receiver: receiver,
                    sent_at: new Date().toISOString(),
                    is_read: false
                };
                console.log(message);

                if (data.content.startsWith('@bot ')) {
                    const command = data.content.substring(5);
                    if (botWs && botWs.readyState === WebSocket.OPEN) {
                        botWs.send(JSON.stringify({
                            type: 'query',
                            data: {
                                message: command
                            },
                            session_id: data.conversation_id,
                        }));
                        console.log(`[Bot] 📤 Sent command to bot: ${command}`);
                    } else {
                        console.error('[Bot] ❌ Bot service is not connected');
                        socket.emit('error', {
                            message: 'Bot service is temporarily unavailable'
                        });
                    }
                }

                const topic = conversation?.type === 'group' ? 'group-chat-messages' : 'private-chat-messages';
                console.log(`[Socket] 📤 Sending message to Kafka topic: ${topic}`);

                await producer.send({
                    topic,
                    messages: [{ value: JSON.stringify(message) }],
                });

                console.log(`[Socket] ✅ Message successfully sent to Kafka`);
                socket.emit('message_sent', { success: true, message });
                io.to(data.conversation_id).emit('new_message', message);

            } catch (error) {
                console.error('[Socket] ❌ Error processing message:', error);
                socket.emit('error', {
                    message: (error instanceof Error ? error.message : 'Failed to send message')
                });
            }
        });

        socket.on('disconnect', async (reason) => {
            console.log(`[Socket] ❌ Client disconnected | ID: ${socket.id} | Reason: ${reason}`);
            const userId = socket.data.userId;
            const conversationId = socket.data.conversationId;
            if (!userId || !conversationId) {
                console.warn(`[Socket] ⚠️ Missing userId or conversationId on disconnect`);
                return;
            }
    
            try {
                const lastMsg = await prisma.messages.findFirst({
                    where: { conversation_id: conversationId },
                    orderBy: { sent_at: 'desc' }
                });
    
                if (lastMsg && lastMsg.sender_id !== userId) {
                    await prisma.conversation_members.update({
                        where: {
                            conversation_id_user_id: {
                                conversation_id: conversationId,
                                user_id: userId
                            }
                        },
                        data: {
                            last_read_message_id: lastMsg.message_id
                        }
                    });
                    console.log(`[Socket] ✅ Updated last_read_message for ${userId}`);
                }
            } catch (error) {
                console.error(`[Socket] ❌ Error updating last_read_message:`, error);
            }
        });
    });
}


function isValidUUID(uuid: string) {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(uuid);
}