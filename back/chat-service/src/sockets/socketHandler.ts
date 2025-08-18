import { PrismaClient } from "@prisma/client";
import { producer } from '../config/kafka';
import { Server, Socket } from "socket.io";
import { randomUUID } from "crypto";
import { authSocket } from "../middleware/authSocket";
import WebSocket from 'ws';

const prisma = new PrismaClient();
let botWs: WebSocket | null = null;

function connectBot(io: Server) {
    if (botWs === null || botWs.readyState === WebSocket.CLOSED) {
        try {
            botWs = new WebSocket('ws://127.0.0.1:3007/api/v1/ws');
            
            botWs.on('open', () => {
                console.log('[Bot] ✅ Connected to bot service');
                // Gửi ping để kiểm tra kết nối
                sendPing();
            });

            botWs.on('close', (code: number, reason: string) => {
                console.log(`[Bot] 🔌 Disconnected from bot service | Code: ${code} | Reason: ${reason}`);
                botWs = null;
                // Thử kết nối lại sau 5 giây
                setTimeout(() => connectBot(io), 5000);
            });

            botWs.on('error', (error) => {
                console.error('[Bot] ❌ WebSocket error:', error);
                if (error.message.includes('ECONNREFUSED')) {
                    console.error('[Bot] ❌ Bot service is not running or not accessible');
                } else if (error.message.includes('ETIMEDOUT')) {
                    console.error('[Bot] ❌ Connection attempt timed out');
                } else if (error.message.includes('ENOTFOUND')) {
                    console.error('[Bot] ❌ Could not resolve host');
                }
            });

            // Thêm xử lý ping/pong để kiểm tra kết nối
            let pingInterval: NodeJS.Timeout;
            let pingTimeout: NodeJS.Timeout;

            function sendPing() {
                if (botWs && botWs.readyState === WebSocket.OPEN) {
                    botWs.send(JSON.stringify({
                        type: 'ping',
                        data: {},
                        message_id: randomUUID(),
                        timestamp: new Date().toISOString()
                    }));

                    // Đặt timeout cho ping
                    pingTimeout = setTimeout(() => {
                        console.error('[Bot] ❌ Ping timeout - no pong received');
                        botWs?.close(1000, 'Ping timeout');
                    }, 5000); // 5 giây timeout cho ping
                }
            }

            botWs.on('message', (data) => {
                try {
                    const response = JSON.parse(data.toString());
                    
                    // Xử lý pong
                    if (response.type === 'pong') {
                        clearTimeout(pingTimeout);
                        return;
                    }

                    // Xử lý error message từ bot
                    if (response.type === 'error') {
                        console.error(`[Bot] ❌ Error from bot service: ${response.data.error}`);
                        if (response.data.code === 'VALIDATION_ERROR') {
                            console.error('[Bot] ❌ Invalid message format sent to bot');
                        }
                        return;
                    }

                    // Xử lý response message
                    if (response.type === 'response' && response.data && response.session_id) {
                        io.to(response.session_id).emit('new_message', {
                            message_id: randomUUID(),
                            conversation_id: response.session_id,
                            sender_id: 'bot',
                            content: response.data.response,
                            sent_at: new Date().toISOString(),
                            is_read: false
                        });
                    }
                } catch (error) {
                    console.error('[Bot] ❌ Error processing bot response:', error);
                    if (error instanceof SyntaxError) {
                        console.error('[Bot] ❌ Invalid JSON received from bot');
                    }
                }
            });

            // Bắt đầu ping định kỳ
            pingInterval = setInterval(sendPing, 30000); // Ping mỗi 30 giây

            // Cleanup khi đóng kết nối
            botWs.on('close', () => {
                clearInterval(pingInterval);
                clearTimeout(pingTimeout);
            });

        } catch (error) {
            console.error('[Bot] ❌ Error creating WebSocket connection:', error);
            setTimeout(() => connectBot(io), 5000);
        }
    }
}

export const handleSocketConnection = (io: Server) => {
    // Khởi tạo kết nối WebSocket với bot service
    connectBot(io);

    io.use(authSocket).on('connection', (socket: Socket) => {
        console.log(`[Socket] ✨ New client connected | ID: ${socket.id}`);
        console.log(`[Socket] 🔑 Auth token:`, socket.handshake.auth);

        socket.on('join_conversation', async (conversationId: string) => {
            try {
                const userId = socket.handshake.auth.token; // Assuming token is user ID
                console.log(`[Socket] 🚪 User ${socket.id} attempting to join conversation ${conversationId}`);
                
                // const isMember = await prisma.conversation_members.findFirst({
                //     where: { conversation_id: conversationId, user_id: userId },
                // });

                // if (!isMember) {
                //     console.warn(`[Socket] ⚠️ User ${socket.id} not authorized for conversation ${conversationId}`);
                //     socket.emit('error', { message: 'Not authorized to join this conversation' });
                //     return;
                // }

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
                // Validate input data
                if (!data.conversation_id || !data.sender_id || !data.content) {
                    console.error('[Socket] ❌ Missing required fields:', data);
                    throw new Error('Missing required fields');
                }

                // Validate UUID format
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
                const message = {
                    message_id: randomUUID(),
                    ...data,
                    sent_at: new Date().toISOString(),
                    is_read: false
                };

                // Check if message starts with @bot
                if (data.content.startsWith('@bot ')) {
                    const command = data.content.substring(5); // Remove '@bot '
                    if (botWs && botWs.readyState === WebSocket.OPEN) {
                        botWs.send(JSON.stringify({
                            type: 'query',
                            data: {
                                message: command
                            },
                            session_id: data.conversation_id,
                            message_id: randomUUID(),
                            timestamp: new Date().toISOString()
                        }));
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

        socket.on('disconnect', (reason) => {
            console.log(`[Socket] ❌ Client disconnected | ID: ${socket.id} | Reason: ${reason}`);
        });
    });
}

// Helper function to validate UUID format
function isValidUUID(uuid: string) {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(uuid);
}