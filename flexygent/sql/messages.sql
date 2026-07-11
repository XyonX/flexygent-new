-- messages.sql


CREATE TABLE IF NOT EXISTS messages(
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    role VARCHAR(200) CHECK (role IN ('user','assistant','tool','system')),
    content TEXT,
    tool_call_provider_id TEXT,
    conversation_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE TRIGGER set_messages_updated_at
    BEFORE UPDATE ON messages
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();