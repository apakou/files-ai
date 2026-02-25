import os

import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted

load_dotenv()

DEFAULT_MODEL = "gemini-3-flash-preview"


def list_available_models() -> list[str]:
    try:
        models = [
            m.name.replace("models/", "")
            for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        return sorted(models)
    except Exception:
        return []


class GeminiClient:

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment. "
                "Add it to your .env file: GOOGLE_API_KEY=your_key_here"
            )

        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str, temperature: float = 0.3) -> str:
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                ),
            )
            return response.text
        except ResourceExhausted as exc:
            raise ResourceExhausted(
                "Gemini API quota exceeded. Your request limit may be "
                "exhausted for today. Check your usage and plan at "
                "https://ai.dev/rate-limit — you may need to wait until the quota "
                "resets or upgrade your plan."
            ) from exc
