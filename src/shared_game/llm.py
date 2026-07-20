from __future__ import annotations

import os
from typing import Any
import requests

SYSTEM_PROMPT = '''You are the guide for a seven-day shared game. Help the player turn one meaningful goal into observable evidence.

Rules:
- Reality outranks the player's explanation.
- Ask for one concrete answer at a time.
- Reflect contradictions without humiliation.
- Do not claim transformation, alignment, or success without evidence.
- Prefer a small experiment over a grand plan.
- Treat misses as useful readings, not moral failures.
- Never invent facts about the player.
- Keep replies under 120 words.

Return only the guide reply, with one observation and one next question.'''

class LLMClient:
    def __init__(self, *, api_key: str | None = None, model: str | None = None, timeout: int = 45):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.model = model or os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")
        self.timeout = timeout
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    @property
    def live(self) -> bool:
        return bool(self.api_key)

    def guide(self, *, stage: str, prompt: str, response: str, history: list[dict[str, Any]], model: str | None = None) -> str:
        if not self.live:
            return self._stub(stage, response)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for item in history[-6:]:
            messages.append({"role": "user", "content": f"Stage: {item['stage']}\nPrompt: {item['prompt']}\nPlayer: {item['response']}"})
            if item.get("guide_reply"):
                messages.append({"role": "assistant", "content": item["guide_reply"]})
        messages.append({"role": "user", "content": f"Current stage: {stage}\nPrompt: {prompt}\nPlayer response: {response}"})
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "X-Title": os.getenv("OPENROUTER_X_TITLE", "Shared Game Agent")}
        referer = os.getenv("OPENROUTER_HTTP_REFERER")
        if referer:
            headers["HTTP-Referer"] = referer
        payload = {"model": model or self.model, "messages": messages, "temperature": 0.3, "max_tokens": 220}
        result = requests.post(self.base_url, headers=headers, json=payload, timeout=self.timeout)
        result.raise_for_status()
        body = result.json()
        return body["choices"][0]["message"]["content"].strip()

    @staticmethod
    def _stub(stage: str, response: str) -> str:
        return f"You recorded: {response.strip()}\nObservation: this is a useful starting artifact, not proof of change.\nNext: make the evidence for the next stage concrete."
