-- tool_calls.sql

CREATE TABLE IF NOT EXISTS tool_calls(
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    provider_call_id TEXT,
    message_id UUID NOT NULL,
    function JSONB NOT NULL ,
    type varchar(50),
    index INTEGER,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS tool_calls_message_id ON tool_calls(message_id);