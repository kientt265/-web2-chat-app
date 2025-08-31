import  { useState } from 'react';
import { useLocation } from 'react-router-dom';
import type { Conversation } from '../../types/index';
import { encryptMessage } from '../../components/HelperSecretChat'
import ChatSidebar from '../../components/chat/ChatSidebar';
import ChatArea from '../../components/chat/ChatArea';
import ConversationForm from '../../components/chat/ConversationForm';
import { useChat } from '../../hooks/useChat';
import {useSocket} from '../../hooks/useSocket';

function Chat() {
  const { conversations, setConversations, messages, setMessages, handleGetMessages } = useChat();
  const location = useLocation();
  const userId = location.state?.user_id;
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [content, setContent] = useState('');
  const [showForm, setShowForm] = useState(false);
  const socketRef = useSocket(userId, setConversations, setMessages, activeConversation);


  const sendMessage = async () => {
    if (!socketRef.current || !activeConversation || !content.trim() || !userId) {
      console.warn('[Chat] ⚠️ Cannot send message: Missing required data', {
        socketConnected: !!socketRef.current,
        hasActiveConversation: !!activeConversation,
        hasContent: !!content.trim(),
        hasUserId: !!userId,
      });
      return;
    }
    const ortherPubkey = activeConversation.members.find((member) => member.user_id !== userId)?.pubkey || '';
    const newMessage = {
      conversation_id: activeConversation.conversation_id,
      sender_id: userId,
      content: (activeConversation.subtype === 'secret') ? await encryptMessage(activeConversation.conversation_id, ortherPubkey, content) : content.trim(),
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
      {activeConversation && (
        <ChatArea
          setConversations={setConversations}
          setActiveConversation={setActiveConversation}
          activeConversation={activeConversation}
          messages={messages}
          userId={userId}
          content={content}
          setContent={setContent}
          sendMessage={sendMessage}
        />
      )}
    </div>
  );
}

export default Chat;