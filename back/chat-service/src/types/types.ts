export interface Message {
    message_id: string;
    conversation_id: string;
    sender_id: string;
    content: string;
    sent_at: string;
    is_read: boolean;
}

export interface ResponeAI {
    type: string;
    data: {
        response: string;
        routed_to: string;
        session_id: string;
        query: string;
        routing_confidence: number;
        routing_reasoning: string;
        routing_method: string;
    };
    processing_time_ms: number;
    timestamp: string; 
}

