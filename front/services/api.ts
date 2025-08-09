import axios from 'axios';
import { authAtom } from '../context/auth.ts';
import { getDefaultStore } from 'jotai';

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
  createConversation: (data: {type: string, name: string, user_ids: string[] }) =>
    api.post('/chat/conversation', data).then((res) => res.data),
  sendMessage: (data: { conversationId: string; content: string }) =>
    api.post('/chat/messages', data).then((res) => res.data),
  getAllConversations: () =>
    api.get('/chat/conversations').then((res) => res.data),
}

