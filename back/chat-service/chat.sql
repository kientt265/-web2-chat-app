
CREATE TYPE conversation_type AS ENUM ('private', 'group');
CREATE TYPE private_type AS ENUM ('normal', 'secret');
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type conversation_type NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE conversations
ADD COLUMN subtype private_type NULL,
ADD CONSTRAINT subtype_private_check
    CHECK (
        (type = 'private' AND subtype IS NOT NULL)
        OR (type <> 'private' AND subtype IS NULL)
    );
ALTER TABLE conversations
ADD CONSTRAINT conversation_name_check
    CHECK (
        (type = 'private' AND name IS NULL)
        OR (type = 'group' AND name IS NOT NULL)
    );
CREATE TABLE conversation_members (
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (conversation_id, user_id)
);
ALTER TABLE conversation_members
ADD COLUMN pubkey TEXT NULL;

ALTER TABLE conversation_members
ADD COLUMN last_read_message_id UUID REFERENCES messages(message_id);

CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    sender_id UUID NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE
);
CREATE TABLE message_deliveries (
    message_id UUID REFERENCES messages(message_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    PRIMARY KEY (message_id, user_id)
);


