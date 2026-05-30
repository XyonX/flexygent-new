from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel,Field
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

load_dotenv()


api_key = os.getenv("API")
base_url = os.getenv("ENDPOINT")

client = OpenAI(api_key=api_key,base_url=base_url)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",extra="ignore",)
    api:str
    endpoint:str


# class LLMClient(BaseModel):

#     s=Settings()

#     def __init__(self):
#         self.client = AsyncOpenAI(api_key=self.s.api , base_url = self.s.endpoint)
    
#     async def complete(self, messages):

#         response = await self.client.chat.completions.create()
