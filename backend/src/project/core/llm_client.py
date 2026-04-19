import os
import json

from openai import AsyncOpenAI


class LLMClient:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

        self.enabled = bool(api_key)
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url) if api_key else None

    async def json_completion(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.enabled or self.client is None:
            raise RuntimeError("LLM disabled")

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content or "{}"
        return json.loads(content)