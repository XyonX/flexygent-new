from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from openai import AsyncOpenAI




class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",extra="ignore",)
    api:str
    endpoint:str

s = Settings()


class LLMClient(BaseModel):

    def __init__(self):
        self.client = AsyncOpenAI(api_key=s.api , base_url = s.endpoint)
    
    async def complete(self, messages):

        response = await self.client.chat.complitions.create()






s1 = Settings()


print(s1.api)
print(s1.endpoint)

