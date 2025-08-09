import React, { useState } from 'react';
import { chatService } from '../../services/api';
import type { Conversation} from '../../types/index';

interface ConversationFormProps {
  setConversations: React.Dispatch<React.SetStateAction<Conversation[]>>;
  setShowForm: (value: boolean) => void;
}

const ConversationForm: React.FC<ConversationFormProps> = ({
  setConversations,
  setShowForm,
}) => {
  const [conversationForm, setConversationForm] = useState({
    type: 'private' as 'private' | 'group',
    name: '',
    user_ids: [] as string[],
  });
  const [usernameInput, setUsernameInput] = useState('');

  const handleCreateConversation = async () => {
    try {
      if (!conversationForm.name.trim() || conversationForm.user_ids.length === 0) {
        console.warn('[Chat] ⚠️ Invalid input: Name and at least one username are required');
        return;
      }

      console.log('[Chat] 📤 Creating new conversation:', conversationForm);
      const newConversation = await chatService.createConversation({
        type: conversationForm.type,
        name: conversationForm.name,
        user_ids: conversationForm.user_ids,
      });

      setConversations((prev) => [...prev, newConversation]);
      setConversationForm({ type: 'private', name: '', user_ids: [] });
      setUsernameInput('');
      setShowForm(false);
      console.log('[Chat] ✅ Conversation created successfully:', newConversation);
    } catch (error) {
      console.error('[Chat] ❌ Failed to create conversation:', error);
    }
  };

  const handleAddUsername = () => {
    if (usernameInput.trim() && !conversationForm.user_ids.includes(usernameInput.trim())) {
      setConversationForm({
        ...conversationForm,
        user_ids: [...conversationForm.user_ids, usernameInput.trim()],
      });
      setUsernameInput('');
    }
  };

  const handleRemoveUsername = (username: string) => {
    setConversationForm({
      ...conversationForm,
      user_ids: conversationForm.user_ids.filter((u) => u !== username),
    });
  };

  return (
    <div className="fixed inset-0 bg-gray-800 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96">
        <h2 className="text-lg font-bold mb-4">Tạo cuộc trò chuyện mới</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleCreateConversation();
          }}
        >
          <div className="flex flex-col gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Loại cuộc trò chuyện</label>
              <select
                className="border rounded-lg px-4 py-2 w-full"
                value={conversationForm.type}
                onChange={(e) =>
                  setConversationForm({
                    ...conversationForm,
                    type: e.target.value as 'private' | 'group',
                  })
                }
              >
                <option value="private">Riêng tư</option>
                <option value="group">Nhóm</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Tên cuộc trò chuyện</label>
              <input
                type="text"
                placeholder="Conversation Name"
                className="border rounded-lg px-4 py-2 w-full"
                value={conversationForm.name}
                onChange={(e) =>
                  setConversationForm({
                    ...conversationForm,
                    name: e.target.value,
                  })
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Thêm thành viên</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Username"
                  className="border rounded-lg px-4 py-2 flex-1"
                  value={usernameInput}
                  onChange={(e) => setUsernameInput(e.target.value)}
                />
                <button
                  type="button"
                  className="bg-blue-500 text-white px-4 py-2 rounded-lg"
                  onClick={handleAddUsername}
                >
                  Thêm
                </button>
              </div>
              <div className="mt-2">
                {conversationForm.user_ids.map((user_ids) => (
                  <div
                    key={user_ids}
                    className="flex items-center justify-between bg-gray-100 p-2 rounded mb-1"
                  >
                    <span>{user_ids}</span>
                    <button
                      type="button"
                      className="text-red-500 hover:text-red-700"
                      onClick={() => handleRemoveUsername(user_ids)}
                    >
                      X
                    </button>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                className="bg-gray-300 px-4 py-2 rounded-lg"
                onClick={() => {
                  setShowForm(false);
                  setConversationForm({ type: 'private', name: '', user_ids: [] });
                  setUsernameInput('');
                }}
              >
                Hủy
              </button>
              <button
                type="submit"
                className="bg-blue-500 text-white px-4 py-2 rounded-lg"
              >
                Tạo
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ConversationForm;