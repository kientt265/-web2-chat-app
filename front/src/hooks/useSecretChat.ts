import { chatService } from '../services/api/api';
import { useCallback } from 'react';
import type { Conversation } from '../types';
import { generateConversationKey, saveKeyLocalStorage} from '../components/HelperSecretChat'

export const useSecretChat =  (
    setConversations: React.Dispatch<React.SetStateAction<Conversation[]>>,
    setActiveConversation: React.Dispatch<React.SetStateAction<Conversation | null>>,
    activeConversation: Conversation | null
) => {
    
    const callAcceptSecretConversation = useCallback(async () => {
        try {
          if (!activeConversation?.conversation_id) {
            console.error("No conversation_id found!");
            return;
          }
          const res = generateConversationKey();
          console.log(res);
          console.log(activeConversation.conversation_id)
          const respone = await chatService.acceptSecretChat({ conversation_id: activeConversation.conversation_id, pubkey: res.pub });
    
          saveKeyLocalStorage(activeConversation.conversation_id, res.priv, res.pub);
    
          const updated = await chatService.getAllConversations();
          setConversations(updated);
    
          const freshConv = updated.find((c: { conversation_id: string; }) => c.conversation_id === activeConversation.conversation_id);
          if (freshConv) {
            setActiveConversation(freshConv);
          }
          console.log(respone);
        } catch (error) {
          console.log('Failed to accept secret conservation!!!', error);
        }
      }, [activeConversation, setConversations, setActiveConversation])
    
      const callRejectSecretConversation = useCallback(async () => {
        try {
          const respone = await chatService.leavingSecretChat(activeConversation ? activeConversation.conversation_id : '');
          const updated = await chatService.getAllConversations();
          setConversations(updated);
          setActiveConversation(null);
          console.log('Reject join secret conservation', respone);
        } catch (error) {
          console.log('Failed to accept secret conservation!!!', error);
        }
      }, []);

      const createConversation = useCallback(
        async (
          type: 'private' | 'group',
          name: string,
          user_ids: { user_id: string; pubkey: string | null }[],
          subtype: 'normal' | 'secret',
          pubkey: string
        ) => {
          try {
            console.log('[Chat] 📤 Creating new conversation:', { type, name, user_ids, subtype, pubkey });
            const newConversation = await chatService.createConversation({
              type,
              name,
              user_ids,
              subtype,
              pubkey,
            });
            saveKeyLocalStorage(newConversation.conversation_id, pubkey, pubkey); // Giả sử pubkey = privkey ở đây, sửa nếu khác
            console.log('[Chat] ✅ Conversation created successfully:', newConversation);
            return newConversation;
          } catch (error) {
            console.error('[Chat] ❌ Failed to create conversation:', error);
            throw error;
          }
        },
        []
      );

      return { callAcceptSecretConversation, callRejectSecretConversation, createConversation };
}