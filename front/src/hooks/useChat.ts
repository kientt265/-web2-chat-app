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

  const updateLastMsg = async (conversation_id: string, user_id: string) => {
    try {
      console.log('[CHAT] Updating message last read msg...');
  
      // Lấy conversation hiện tại
      const targetConv = conversations.find((c) => c.conversation_id === conversation_id);
      if (!targetConv || !targetConv.last_message) return;
  
      const lastMsgId = targetConv.last_message.message_id;
  
      await chatService.updateLastMsg({ conversation_id, last_read_message_id: lastMsgId });
  
      setConversations((prev) =>
        prev.map((conv) =>
          conv.conversation_id === conversation_id
            ? {
                ...conv,
                members: conv.members.map((mem) =>
                  mem.user_id === user_id
                    ? { ...mem, last_read_message_id: lastMsgId } // đúng user đang đọc
                    : mem
                ),
              }
            : conv
        )
      );
      
    } catch (error) {
      console.error('[CHAT] ❌ Failed to update last msg:', error);
    }
  };
  

  return { conversations, setConversations, messages, setMessages, handleGetMessages, updateLastMsg };
};