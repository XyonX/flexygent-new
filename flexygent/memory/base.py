from abc import ABC, abstractmethod
from flexygent.types import Conversation
class ConversationMemory(ABC):
    
    @abstractmethod
    def save(self,conversation:Conversation,name):
        ...
    @abstractmethod
    def load(self,name):
        ...
    @abstractmethod
    def list_saved(self)->list[str]:
        ...
    @abstractmethod
    def delete(self,name):
        ...
    @abstractmethod
    def exists(self,name):
        ...