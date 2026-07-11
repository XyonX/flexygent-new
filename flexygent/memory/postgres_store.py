from flexygent.memory import ConversationMemory
import psycopg



class PostgresStore(ConversationMemory):
    def __init__(self,connection_string:str, table_name:str = "conversations"):
        self.conn = psycopg(connection_string)
        self.conversation = self.conn.cursor()
        self.table_name=table_name

    def __del__(self):
        self.conn.close()
        self.conversation.close()

    def _ensure_table():
        pass
    
    def list_saved(self,user_id=None):
        query = "SELECT * FROM %s"
        self.conversation.execute(query,(self.table_name))
        conversations = self.conversation.fetchall()
        return conversations
