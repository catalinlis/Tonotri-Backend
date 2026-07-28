from openai import OpenAI
from django.conf import settings

class OpenAIClient:

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_json(self, model: str, prompt: str, schema: dict):
        response = self.client.responses.create(
            model=model,
            input=prompt,
            text={
                'format': {
                    'type': 'json_schema',
                    'name': 'country_schema',
                    'schema': schema
                }
            }
        )

        return response.output_text