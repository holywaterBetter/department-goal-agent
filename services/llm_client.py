from __future__ import annotations

import os
import time
from dataclasses import dataclass

import requests
from dotenv import load_dotenv


class LLMClientError(RuntimeError):
    """Raised when LLM requests fail after retries."""


@dataclass
class LLMClient:
    api_base_url: str
    api_key: str
    model_name: str
    timeout: float
    max_retries: int = 3
    backoff_base_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "LLMClient":
        load_dotenv()
        api_base_url = os.getenv("LLM_API_BASE_URL", "").strip()
        api_key = os.getenv("LLM_API_KEY", "").strip()
        model_name = os.getenv("LLM_MODEL_NAME", "").strip()

        timeout_raw = os.getenv("LLM_TIMEOUT", "60").strip() or "60"
        try:
            timeout = float(timeout_raw)
        except ValueError as exc:
            raise ValueError(f"Invalid LLM_TIMEOUT value: {timeout_raw}") from exc

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

        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.api_base_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                if self._is_retryable_status(response.status_code):
                    raise requests.HTTPError(
                        f"Retryable HTTP status: {response.status_code}",
                        response=response,
                    )

                response.raise_for_status()
                data = response.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise LLMClientError(f"Unexpected LLM response format: {data}") from exc

            except requests.Timeout as exc:
                last_error = LLMClientError(
                    f"LLM request timed out after {self.timeout} seconds (attempt {attempt}/{self.max_retries})."
                )
            except requests.ConnectionError as exc:
                last_error = LLMClientError(
                    f"LLM network connection failed (attempt {attempt}/{self.max_retries}): {exc}"
                )
            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code is not None and not self._is_retryable_status(status_code):
                    raise LLMClientError(
                        f"Non-retryable LLM HTTP error: {status_code} {exc.response.text}"
                    ) from exc
                last_error = LLMClientError(
                    f"Retryable LLM HTTP error (attempt {attempt}/{self.max_retries}): {status_code}"
                )
            except requests.RequestException as exc:
                raise LLMClientError(f"Unexpected request failure while calling LLM API: {exc}") from exc

            if attempt < self.max_retries:
                sleep_seconds = self.backoff_base_seconds * (2 ** (attempt - 1))
                time.sleep(sleep_seconds)

        raise LLMClientError(f"LLM request failed after {self.max_retries} attempts: {last_error}")

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        return status_code == 429 or 500 <= status_code < 600
