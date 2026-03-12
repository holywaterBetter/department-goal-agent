from __future__ import annotations

import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv


@dataclass
class LLMClient:
    api_base_url: str
    api_key: str
    model_name: str
    timeout: float

    @classmethod
    def from_env(cls) -> "LLMClient":
        load_dotenv()
        api_base_url = os.getenv("LLM_API_BASE_URL", "").strip()
        api_key = os.getenv("LLM_API_KEY", "").strip()
        model_name = os.getenv("LLM_MODEL_NAME", "").strip()
        timeout = float(os.getenv("LLM_TIMEOUT", "60") or 60)

        missing = [
            name
            for name, value in {
                "LLM_API_BASE_URL": api_base_url,
                "LLM_API_KEY": api_key,
                "LLM_MODEL_NAME": model_name,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return cls(
            api_base_url=api_base_url,
            api_key=api_key,
            model_name=model_name,
            timeout=timeout,
        )

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a helpful enterprise planning assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            self.api_base_url,
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"Unexpected LLM response format: {data}") from exc
