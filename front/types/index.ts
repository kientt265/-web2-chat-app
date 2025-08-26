export interface User {
    id?: string;
    email: string;
    username: string;
    password: string; 
    createdAt?: string;
    updatedAt?: string;
}

export interface Message {
    message_id: string;
    conversation_id: string;
    sender_id: string;
    content: string;
    sent_at: string;
    is_read: boolean;
}


export interface ConversationMember {
    conversation_id: string;
    user_id: string;
    joined_at: string;
}

export interface Conversation {
    conversation_id: string;
    type: 'group' | 'private';
    subtype: 'normal' | 'secret';
    name: string;
    created_at: string;
    member_count: number;
    members: ConversationMember[];
    last_message: Message | null;
}
export interface UserMember {
    user_id: string;
    pubkey: string | null;
  };
