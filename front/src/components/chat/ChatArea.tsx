import React, { useState, useEffect } from 'react';
import type { Conversation, Message } from '../../types/index';
import { useSecretChat } from '../../hooks/useSecretChat';
import { useMessages } from '../../hooks/useMessages';
import { decryptMessage } from '../../components/HelperSecretChat'
interface ChatAreaProps {
  setConversations: React.Dispatch<React.SetStateAction<Conversation[]>>;
  setActiveConversation: React.Dispatch<React.SetStateAction<Conversation | null>>;
  activeConversation: Conversation;
  messages: Message[];
  userId: string | undefined;
  content: string;
  setContent: (value: string) => void;
  sendMessage: () => void;
}

const ChatArea: React.FC<ChatAreaProps> = ({
  setConversations,
  setActiveConversation,
  activeConversation,
  messages,
  userId,
  content,
  setContent,
  sendMessage,
}) => {
  const [decryptedMessages, setDecryptedMessages] = useState<Message[]>([]);
  const ortherPubkey = activeConversation.members.find((member) => member.user_id !== userId)?.pubkey || '';
  const { callAcceptSecretConversation, callRejectSecretConversation } = useSecretChat(
    setConversations,
    setActiveConversation, 
    activeConversation
  );

  useEffect(() => {
    const processMessages = async () => {
      if (activeConversation.subtype === 'secret') {
        const results = await Promise.all(
          messages.map(async (msg) => ({
            ...msg,
            content: await decryptMessage(activeConversation.conversation_id, ortherPubkey, msg.content),
          }))
        );
        setDecryptedMessages(results);
      } else {
        setDecryptedMessages(messages);
      }
    };

    processMessages();
  }, [messages, activeConversation]);

  return (
    <div className="flex-1 flex flex-col">
      {activeConversation ? (
        <>
          <div className="p-4 border-b">
            <h2 className="text-xl font-bold">{activeConversation.name ? activeConversation.name : "Secret Chat"}</h2>
            <div className="flex items-center gap-5">
              <p className="text-sm text-gray-500">
                {activeConversation.member_count} members
              </p>
              {(activeConversation.subtype === "secret" && activeConversation.members.find(member => member.user_id === userId)?.pubkey === null) ? (
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <span>Có người muốn tạo cuộc trò chuyện bí mật với bạn</span>

                  <button
                    onClick={callAcceptSecretConversation}
                    className="px-2 py-1 bg-green-500 text-white rounded hover:bg-green-600 cursor:pointer"
                  >
                    ✓
                  </button>

                  <button
                    onClick={callRejectSecretConversation}
                    className="px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600 cursor:pointer"
                  >
                    ✕
                  </button>
                </div>
              ) : null}
            </div>


          </div>
          {/* // Cách hiện tại - không hoạt động đúng với async */}
          <div className="flex-1 overflow-y-auto p-4">

            {decryptedMessages.map((msg) => (
              <div
                key={`${msg.message_id}-${msg.sent_at}`}
                className={`mb-4 flex ${msg.sender_id === userId ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`rounded-lg p-3 max-w-[70%] ${msg.sender_id === userId ? 'bg-blue-500 text-white' : 'bg-gray-100'
                    }`}
                >
                  <div className="text-sm">{msg.content}</div>
                  <div className="text-xs opacity-75 mt-1">
                    {new Date(msg.sent_at).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}

          </div>
          <div className="p-4 border-t">
            <div className="flex gap-2">
              <input
                className="flex-1 border rounded-lg px-4 py-2"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Type a message"
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              />

              <button
                className="bg-blue-500 text-white px-4 py-2 rounded-lg"
                onClick={sendMessage}
              >
                Send
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center text-gray-500">
          Select a conversation to start chatting
        </div>
      )}
    </div>
  );
};

export default ChatArea;
