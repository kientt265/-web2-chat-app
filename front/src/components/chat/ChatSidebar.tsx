import React from "react";
import type { Conversation } from "../../types/index";

interface ChatSidebarProps {
  userId: string;
  conversations: Conversation[];
  activeConversation: Conversation | null;
  handleConversationClick: (conv: Conversation) => void;
  setShowForm: (value: boolean) => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  userId,
  conversations,
  activeConversation,
  handleConversationClick,
  setShowForm,
}) => {
  return (
    <div className="w-1/4 bg-gray-100 border-r overflow-y-auto">
      <div className="p-4 border-b">
        <button
          className="bg-blue-500 hover:bg-blue-700 text-white rounded p-2 cursor-pointer"
          onClick={() => setShowForm(true)}
        >
          Thêm cuộc trò chuyện
        </button>
      </div>

      <div className="divide-y">
        {conversations.map((conv) => {
          const member = conv.members.find((mem) => mem.user_id === userId);
          const isUnread =
            conv.last_message?.message_id !== member?.last_read_message_id;
          return (
            <div
              key={conv.conversation_id}
              className={`p-4 cursor-pointer hover:bg-gray-200 ${activeConversation?.conversation_id === conv.conversation_id
                ? "bg-gray-200"
                : ""
                }`}
              onClick={() => handleConversationClick(conv)}
            >
              <h3 className="font-semibold">
                {conv.name ? conv.name : conv.conversation_id}
              </h3>

              <p
                className={`text-sm truncate ${isUnread ? 'font-bold text-black' : 'font-normal text-gray-500'
                  }`}
              >
                {conv.subtype === 'secret' && conv.last_message?.content
                  ? 'Click to show secret msg'
                  : conv.last_message?.content || 'No messages yet'}
              </p>



              <p className="text-xs text-gray-400">
                {conv.last_message
                  ? new Date(conv.last_message.sent_at).toLocaleDateString()
                  : ""}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ChatSidebar;
