from abc import ABC, abstractmethod
from flexygent.types import Conversation
class ConversationMemory(ABC):
    
    @abstractmethod
    def save(self,conversation:Conversation,name,user_id = None):
        ...
    @abstractmethod
    def load(self,name:str, user_id=None):
        ...
    @abstractmethod
    def list_saved(self,user_id=None)->list[str]:
        ...
    @abstractmethod
    def delete(self,name, user_id = None):
        ...
    @abstractmethod
    def exists(self,name,user_id =None):
        ...