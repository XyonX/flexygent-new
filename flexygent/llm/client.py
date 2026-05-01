from openai import AsyncOpenAI
from flexygent.core.config import settings
from flexygent.core.types import Message

class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key = settings.openrouter_api_key, base_url = settings.openrouter_base_url)

        self.model = settings.default_model

    async def complete(self,messages:list[Message] , system: str | None = None)->str:
        # build the list as as plain dict for api
        payload =[]
        if system:
            payload.append({"role":"system","content":system})
        
        payload.extend([m.to_dict()  for m in messages])

        response = await self.client.chat.completions.create(model =self.model,messages=payload)

        return response.choices[0].message.content
    
    async def stream(self,messages:list[Message], system :str |None =None):

        # build the list as plain dict for apiu

        payload = []

        if system:
            payload.append({"role":"system", "content":system})

        payload.extend([m.to_dict() for m in messages])

        response = await self.client.chat.completions.create(model=self.model,messages=payload, stream =True)

        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta is not None:
                yield delta


