import httpx

class GeminiProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-2.5-flash"
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def get_provider_name(self):
        return "gemini"

    def format_messages(self, system_prompt, user_prompt):
        # Gemini expects a single content with the full prompt
        prompt = f"{system_prompt}\n{user_prompt}"
        return {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

    async def chat_completion(self, messages, max_tokens=1000):
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }
        data = {
            "contents": messages["contents"]
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.url, headers=headers, json=data)
                resp.raise_for_status()
                result = resp.json()
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "success": True,
                    "content": content,
                    "usage": {}
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }

    def get_config_info(self):
        return {
            "provider": "gemini",
            "model": self.model
        }