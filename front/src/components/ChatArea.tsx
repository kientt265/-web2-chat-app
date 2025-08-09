import React from 'react';
import type { Conversation, Message } from '../../types/index';

interface ChatAreaProps {
  activeConversation: Conversation | null;
  messages: Message[];
  userId: string | undefined;
  content: string;
  setContent: (value: string) => void;
  sendMessage: () => void;
}

const ChatArea: React.FC<ChatAreaProps> = ({
  activeConversation,
  messages,
  userId,
  content,
  setContent,
  sendMessage,
}) => {
  return (
    <div className="flex-1 flex flex-col">
      {activeConversation ? (
        <>
          <div className="p-4 border-b">
            <h2 className="text-xl font-bold">{activeConversation.name}</h2>
            <p className="text-sm text-gray-500">
              {activeConversation.member_count} members
            </p>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {messages.map((msg) => (
              <div
                key={`${msg.message_id}-${msg.sent_at}`}
                className={`mb-4 flex ${
                  msg.sender_id === userId ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`rounded-lg p-3 max-w-[70%] ${
                    msg.sender_id === userId ? 'bg-blue-500 text-white' : 'bg-gray-100'
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