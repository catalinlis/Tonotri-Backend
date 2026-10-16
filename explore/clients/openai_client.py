from openai import OpenAI
from django.conf import settings
from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedJSON:
    """Hold structured output and its token usage."""

    output_text: str
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int

class OpenAIClient:
    """Generate schema-constrained JSON through the OpenAI Responses API."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_json(self, model: str, prompt: str, schema: dict):
        """Generate JSON and return its text with usage metadata."""

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

        usage = response.usage
        input_details = getattr(usage, 'input_tokens_details', None)

        return GeneratedJSON(
            output_text=response.output_text,
            input_tokens=usage.input_tokens,
            cached_input_tokens=getattr(input_details, 'cached_tokens', 0) or 0,
            output_tokens=usage.output_tokens,
        )
