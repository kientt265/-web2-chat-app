import { useEffect, useRef } from 'react';
import io from 'socket.io-client';
import type { Conversation, Message } from '../types';

export const useSocket = (
  userId: string,
  setConversations: React.Dispatch<React.SetStateAction<Conversation[]>>,
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>,
  activeConversation: Conversation | null
) => {
  const socketRef = useRef<any>(null);

  useEffect(() => {
    const socket = io('http://localhost:3002', {
      path: '/socket.io',
      transports: ['websocket'],
      auth: { token: 'your-secret-key' },
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('[Socket] ✅ Connected successfully');
      socket.emit('join-app', userId);
    });

    socket.on('new_conversation', (conversation: any) => {
      console.log('[Socket] 🆕 New conversation:', conversation);
      setConversations((prev) =>
        prev.some((c) => c.conversation_id === conversation.conversation_id)
          ? prev
          : [
            {
              conversation_id: conversation.conversation_id,
              type: conversation.type,
              subtype: conversation.subtype,
              name: conversation.name,
              created_at: conversation.created_at,
              member_count: conversation.members?.length,
              members: conversation.members,
              last_message: null
            },
            ...prev
          ]
      );
    });

    socket.on('new_msg_socker_user_personal', (message: Message) => {
      console.log('[Socket-Personal] 📩 Real-time message received:', message);
      if(activeConversation?.conversation_id !== message.conversation_id) {
        console.log('1', activeConversation?.conversation_id);
        console.log('2', message.conversation_id);
        setConversations((prev) =>
          prev.map((conv) =>
            conv.conversation_id === message.conversation_id
              ? {
                ...conv,
                last_message: conv.last_message
                  ? { ...conv.last_message, message_id: message.message_id }
                  : { ...message },
              }
              : conv
          )
        );
      }

    });

    socket.on('new_message', (message: Message) => {
      console.log('[Socket] 📩 Real-time message received:', message);
      setMessages((prev) => {
        const messageExists = prev.some((msg) => msg.message_id === message.message_id);
        if (messageExists) {
          console.log('[Chat] ⚠️ Duplicate message detected:', message.message_id);
          return prev;
        }
        return [...prev, message];
      });
    });

    return () => {
      socket.disconnect();
    };
  }, [userId, setConversations, setMessages]);

  useEffect(() => {
    if (activeConversation && socketRef.current) {
      console.log('[Chat] 🔗 Joining conversation:', activeConversation.conversation_id);
      socketRef.current.emit('join_conversation', activeConversation.conversation_id);
    }
  }, [activeConversation]);

  return socketRef;
};