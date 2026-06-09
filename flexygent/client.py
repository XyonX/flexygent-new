from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel,Field
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

load_dotenv()


api_key = os.getenv("API")
base_url = os.getenv("ENDPOINT")

cloudflare_api_key= os.getenv("CLOUDFLARE_API_KEY")       # your API token
cloduflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID") # your account ID

cloudflare_base_url=f"https://api.cloudflare.com/client/v4/accounts/{cloduflare_account_id}/ai/v1"

client = OpenAI(api_key=cloudflare_api_key,base_url=cloudflare_base_url)


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
