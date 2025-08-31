import React, { useState, useEffect } from 'react';
import type { Conversation, Message } from '../../types/index';
import { useSecretChat } from '../../hooks/useSecretChat';
import { useMessages } from '../../hooks/useMessages';
import { decryptMessage } from '../../components/HelperSecretChat'
import more_logo from '../../assets/more.png';
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
  const [showSidebar, setShowSidebar] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
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
          {showConfirm && (
            <div className="fixed inset-0 flex items-center justify-center bg-black/30 backdrop-blur-sm z-50">
              <div className="bg-white rounded-lg shadow-lg p-6 w-80">
                <h2 className="text-lg font-semibold mb-4">Xác nhận</h2>
                <p className="text-sm text-gray-600 mb-6">
                  Bạn có chắc chắn muốn rời nhóm không?
                </p>
                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => setShowConfirm(false)}
                    className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 cursor-pointer"
                  >
                    Hủy
                  </button>
                  <button
                    onClick={() => {
                      callRejectSecretConversation();
                      setShowConfirm(false);
                    }}
                    className="px-4 py-2 rounded bg-red-500 text-white hover:bg-red-600 cursor-pointer"
                  >
                    Xác nhận
                  </button>
                </div>
              </div>
            </div>
          )}
          <div className="flex items-center justify-between p-4 border-b">

            <div className="p-4 ">
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

            <div>
              <button onClick={() => setShowSidebar(true)}>
                <img src={more_logo} alt="More" className="w-6 h-6 cursor-pointer" />
              </button>
            </div>
          </div>

          <div
            className={`fixed top-0 right-0 h-full w-64 bg-white shadow-lg transform transition-transform duration-300 z-40 ${showSidebar ? "translate-x-0" : "translate-x-full"}`}>
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="text-lg font-semibold">Tùy chọn</h3>
              <button onClick={() => setShowSidebar(false)} className="text-gray-500 hover:text-gray-700">
                ✕
              </button>
            </div>
            <div className="p-4">
              <p className="mb-2">Thông tin cuộc trò chuyện</p>
              <p className="mb-2">Danh sách thành viên</p>
              <p onClick={() => setShowConfirm(true)} className="mb-2 bg-red-500 rounded p-1 cursor-pointer">Rời nhóm</p>
            </div>
          </div>
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
