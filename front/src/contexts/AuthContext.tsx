import { atom } from 'jotai';
import type { User } from '../types/index.ts';

interface AuthState {
  token: string | null;
  user: User | null;
} 

export const authAtom = atom<AuthState>({ token: null, user: null });