import { useEffect, useState } from 'react';
import type { Conversation, Message } from '../types';
import { decryptMessage } from '../components/HelperSecretChat';

export const useMessages = (activeConversation: Conversation | null, messages: Message[]) => {
  const [decryptedMessages, setDecryptedMessages] = useState<Message[]>([]);
  const ortherPubkey =
    activeConversation?.members.find((member) => member.user_id !== member.user_id)?.pubkey || '';

  useEffect(() => {
    const processMessages = async () => {
      if (activeConversation?.subtype === 'secret') {
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
  }, [messages, activeConversation, ortherPubkey]);

  return decryptedMessages;
};