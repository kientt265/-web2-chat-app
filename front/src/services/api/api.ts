import axios from 'axios';
import { authAtom } from '../../contexts/AuthContext.tsx';
import { getDefaultStore } from 'jotai';
import type { UserMember } from '../../types/index.ts';

const store = getDefaultStore();

const api = axios.create({
  baseURL: 'http://localhost:80/api/',
});

api.interceptors.request.use((config) => {
  const auth = store.get(authAtom);
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`;
  }
  return config;
});

export const userService = {
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data).then((res) => res.data),
  register: (data: { username: string; email: string; password: string }) =>
    api.post('/auth/register', data).then((res) => res.data),
}

export const chatService = {
  getMessages: (conversationId: string) =>
    api.get(`/chat/messages/${conversationId}`).then((res) => res.data),
  createConversation: (data: { type: string, name?: string, user_ids: UserMember[], subtype?: string, pubkey?: string }) =>
    api.post('/chat/conversation', data).then((res) => res.data),
  sendMessage: (data: { conversationId: string; content: string }) =>
    api.post('/chat/messages', data).then((res) => res.data),
  getAllConversations: () =>
    api.get('/chat/conversations').then((res) => res.data),
  acceptSecretChat: (data: { conversation_id: string; pubkey: string }) =>
    api
      .patch(`/chat/conversations/${data.conversation_id}/accept`, data)
      .then((res) => res.data),
  leavingSecretChat: (conversationId: string) =>
    api.delete(`/chat/conversations/${conversationId}`).then((res) => res.data),
  uploadImage: (formData: FormData, conversation_id: string) =>
    api.post(`/chat/conversations/${conversation_id}/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((res) => res.data),
  updateLastMsg: (data: {conversation_id: string, last_read_message_id: string}) =>
    api.post(`/chat/conversations/update_last_read_msg`, data).then((res) => res.data),
  addNewUserGroup: (data: {conversation_id: string, user_added_id: string}) => 
    api.post(`/chat/'conversations/add_new_user_group`, data).then((res) => res.data),

}
// const { type, name, user_ids, subtype, pubkey } = req.body as {
//   type: 'private' | 'group';
//   name?: string;
//   user_ids: UserMember[];
//   subtype?: 'normal' | 'secret';
//   pubkey?: string;
// };

