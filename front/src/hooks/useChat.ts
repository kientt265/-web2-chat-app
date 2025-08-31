import { useEffect, useState } from 'react';
import { chatService } from '../services/api/api';
import type { Conversation, Message } from '../types';

export const useChat = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const data = await chatService.getAllConversations();
        console.log(data);
        setConversations(data);
      } catch (error) {
        console.error('Failed to fetch conversations:', error);
      }
    };
    fetchConversations();
  }, []);

  const handleGetMessages = async (conversationId: string) => {
    try {
      console.log('[Chat] 📥 Fetching message history...');
      const historicalMessages = await chatService.getMessages(conversationId);
      setMessages(historicalMessages);
      console.log(`[Chat] ✅ Loaded ${historicalMessages.length} historical messages`);
    } catch (error) {
      console.error('[Chat] ❌ Failed to fetch messages:', error);
    }
  };

  return { conversations, setConversations, messages, setMessages, handleGetMessages };
};