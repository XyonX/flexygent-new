from flexygent.memory.base import ConversationMemory
from flexygent.types import Conversation
from datetime import datetime
import json
from pathlib import Path

class FileStore(ConversationMemory):

    def __init__(self,base_dir="conversations"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self,file_name):
        return self.base_dir / file_name

    def gen_file_name(self,base_path="conversations")->str:
        dt = datetime.now()
        file_name = f"conversation-{dt.strftime('%Y-%m-%d_%H-%M-%S')}.json"
        return file_name

    def save(self,conversation:Conversation,file_name:str):

        path = self._get_full_path(file_name)
        conversation_dump = conversation.model_dump()
        with open(path,"w",encoding="utf-8") as file:
            json.dump(conversation_dump,file,indent=4)
    
    def load(self,file_name):
        path = self._get_full_path(file_name)
        with open(path,"r",encoding="utf-8") as file:
            data = json.load(file)
        return Conversation.model_validate(data)

    def list_saved(self)->list[str]:
        pattern = "conversation-*.json"
        files = self.base_dir.glob(pattern)
        return sorted([f.name for f in files],reverse=True)

    def delete(self, file_name):
        print("aa")

    def exists(self, file_name):
        print("aa")







