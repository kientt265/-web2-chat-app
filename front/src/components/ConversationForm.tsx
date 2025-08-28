import React, { useState } from 'react';
import { chatService } from '../../services/api';
import type { Conversation } from '../../types/index';
import { generateConversationKey, saveKeyLocalStorage } from './HelperSecretChat';

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
    user_ids: [] as { user_id: string; pubkey: string | null }[],
    subtype: 'normal' as 'normal' | 'secret',
  });
  const [key, setKey] = useState<{ pubkey: string, privkey: string }>({
    pubkey: '',
    privkey: ''
  })
  const [onHandle, setOnHandle] = useState(false);
  const [usernameInput, setUsernameInput] = useState<{ user_id: string; pubkey: string | null }>({
    user_id: '',
    pubkey: null,
  });


  const handleCreateConversation = async () => {
    try {


      console.log('[Chat] 📤 Creating new conversation:', conversationForm);
      const newConversation = await chatService.createConversation({
        type: conversationForm.type,
        name: conversationForm.name,
        user_ids: conversationForm.user_ids,
        subtype: conversationForm.subtype,
        pubkey: key.pubkey
      });

      setConversations((prev) => [...prev, newConversation]);
      saveKeyLocalStorage(newConversation.conversation_id, key.privkey, key.pubkey);
      setConversationForm({ type: 'private', name: '', user_ids: [], subtype: 'normal' });
      setUsernameInput({ user_id: '', pubkey: null });
      setShowForm(false);
      console.log('[Chat] ✅ Conversation created successfully:', newConversation);
    } catch (error) {
      console.error('[Chat] ❌ Failed to create conversation:', error);
    }
  };

  const handleAddUsername = () => {
    if (
      usernameInput.user_id.trim() &&
      !conversationForm.user_ids.some((u) => u.user_id === usernameInput.user_id.trim())
    ) {
      setConversationForm({
        ...conversationForm,
        user_ids: [...conversationForm.user_ids, { ...usernameInput, user_id: usernameInput.user_id.trim() }],
      });
      setUsernameInput({ user_id: '', pubkey: null });
    }
  };


  const handleRemoveUsername = (user_id: string) => {
    setConversationForm({
      ...conversationForm,
      user_ids: conversationForm.user_ids.filter((u) => u.user_id !== user_id),
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
                onChange={(e) => {
                  const value = e.target.value as 'private' | 'group';
                  setConversationForm({
                    ...conversationForm,
                    type: value,
                  });
                  setOnHandle(value === 'group');
                }
                }
              >
                <option value="private">Riêng tư</option>
                <option value="group">Nhóm</option>
              </select>
            </div>

            {
              onHandle ?
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
                </div> :
                <div>
                  <label className="block text-sm font-medium mb-1">Loại cuộc trò chuyện 1:1</label>
                  <select
                    className="border rounded-lg px-4 py-2 w-full"
                    value={conversationForm.subtype}
                    onChange={(e) => {
                      const value = e.target.value as 'normal' | 'secret';
                      setConversationForm({
                        ...conversationForm,
                        subtype: value,
                      });
                      const res = generateConversationKey();
                      setKey({ pubkey: res.pub, privkey: res.priv });
                    }
                    }
                  >
                    <option value="normal">Bình thường</option>
                    <option value="secret">Siêu bảo mật</option>
                  </select>
                </div>
            }
            <div>
              <label className="block text-sm font-medium mb-1">Thêm thành viên</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Username"
                  className="border rounded-lg px-4 py-2 flex-1"
                  value={usernameInput.user_id}
                  onChange={(e) =>
                    setUsernameInput({
                      ...usernameInput,
                      user_id: e.target.value,
                    })
                  }
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
                {conversationForm.user_ids.map((user) => (
                  <div
                    key={user.user_id}
                    className="flex items-center justify-between bg-gray-100 p-2 rounded mb-1"
                  >
                    <span>{user.user_id}</span>
                    <button
                      type="button"
                      className="text-red-500 hover:text-red-700"
                      onClick={() => handleRemoveUsername(user.user_id)}
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
                  setConversationForm({ type: 'private', name: '', user_ids: [], subtype: 'normal' });
                  setUsernameInput({ user_id: '', pubkey: null });
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