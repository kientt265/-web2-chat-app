import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import io from 'socket.io-client';
import { chatService } from '../../services/api';
import type { Conversation} from '../../types/index';
import type { Message } from '../../types/index';
import ChatSidebar from './ChatSidebar';
import ChatArea from './ChatArea';
import ConversationForm from './ConversationForm';

function Chat() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [content, setContent] = useState('');
  const socketRef = React.useRef<any>(null);
  const botSocketRef = React.useRef<WebSocket | null>(null);
  const [showForm, setShowForm] = useState(false);
  const location = useLocation();
  const userId = location.state?.user_id;

  // Fetch conversations
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const data = await chatService.getAllConversations();
        setConversations(data);
      } catch (error) {
        console.error('Failed to fetch conversations:', error);
      }
    };
    fetchConversations();
  }, []);

  

  // Socket effect for real-time messages
  useEffect(() => {
    if (!activeConversation) return;

    const socket = io('http://localhost:3002', {
      path: '/socket.io',
      transports: ['websocket'],
      auth: { token: 'your-secret-key' },
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('[Socket] ✅ Connected successfully');
      socket.emit('join_conversation', activeConversation.conversation_id);
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
      setMessages([]);
    };
  }, [activeConversation]);


  useEffect(() => {
  const botSocket = new WebSocket("ws://localhost:3007/api/v1/ws");

  botSocket.onopen = () => console.log("[BotSocket] ✅ Connected");

  botSocket.onmessage = (event) => {
    const botMessage = JSON.parse(event.data);
    // Bot trả lời → add vào box đang active
    // setMessages((prev) => [
    //   ...prev,
    //   {
    //     conversation_id: activeConversation?.conversation_id,
    //     sender_id: "ChatBot",
    //     content: botMessage.content,
    //     message_id: botMessage.message_id || Date.now().toString(),
    //   },
    // ]);
  };

  botSocketRef.current = botSocket;

  return () => {
    botSocket.close();
  };
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

  const sendMessage = () => {
    if (!socketRef.current || !activeConversation || !content.trim() || !userId) {
      console.warn('[Chat] ⚠️ Cannot send message: Missing required data', {
        socketConnected: !!socketRef.current,
        hasActiveConversation: !!activeConversation,
        hasContent: !!content.trim(),
        hasUserId: !!userId,
      });
      return;
    }

    const newMessage = {
      conversation_id: activeConversation.conversation_id,
      sender_id: userId,
      content: content.trim(),
    };

    console.log('[Chat] 📤 Attempting to send message:', newMessage);
    socketRef.current.emit('send_message', newMessage);
    setContent('');
  };

  const handleConversationClick = async (conv: Conversation) => {
    setActiveConversation(conv);
    await handleGetMessages(conv.conversation_id);
  };

  return (
    <div className="flex h-screen">
      {showForm && (
        <ConversationForm
          setConversations={setConversations}
          setShowForm={setShowForm}
        />
      )}
      <ChatSidebar
        conversations={conversations}
        activeConversation={activeConversation}
        handleConversationClick={handleConversationClick}
        setShowForm={setShowForm}
      />
      <ChatArea
        activeConversation={activeConversation}
        messages={messages}
        userId={userId}
        content={content}
        setContent={setContent}
        sendMessage={sendMessage}
      />
    </div>
  );
}

export default Chat;