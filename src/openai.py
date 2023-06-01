import openai, os
from dotenv import load_dotenv
from typing import List
import src.logs as logs

class Role:
    USER = "user"
    SYSTEM = "system"

class Message:
    def __init__(self, role: Role | int, content: str) -> None:
        self.role = role
        self.content = content

class OpenAI:
    __api_key = None
    logger = None

    def __load_api_key(self):
        if not self.__api_key:
            load_dotenv()
            self.__api_key = os.environ.get("OPENAI_KEY")
            self.logger = logs.init_logger()

    @classmethod
    def chat_response(cls, messages: List[Message], max_tokens: int = 50):
        cls.__load_api_key(cls)
        cls.logger.info("Making AI Chat Request")

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": message.role, "content": message.content} for message in messages],
            max_tokens = max_tokens,
            api_key = cls.__api_key
        )

        generated_text = response.choices[0]['message']['content']
        if generated_text.startswith('"') and generated_text.endswith('"'):
            generated_text = generated_text[1:-1]

        return generated_text

    @classmethod
    def moderation(cls, input):
        cls.__load_api_key(cls)
        cls.logger.info("Making AI Moderation Request")

        response = openai.Moderation.create(
            input=input,
            model="text-moderation-stable",
            api_key = cls.__api_key
        )

        return response['results'][0]