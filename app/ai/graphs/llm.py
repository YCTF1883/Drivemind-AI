import json

import httpx

from app.ai.exceptions import AIServiceError
from app.settings.config import settings


async def call_deepseek_json(system: str, prompt: str) -> dict:
    url = settings.DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": settings.DEEPSEEK_MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }
    try:
        async with httpx.AsyncClient(timeout=settings.DEEPSEEK_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise AIServiceError(f"DeepSeek API 调用失败：{exc.response.status_code} {exc.response.text}") from exc
    except httpx.HTTPError as exc:
        raise AIServiceError(f"DeepSeek API 网络异常：{exc}") from exc

    data = response.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not text:
        raise AIServiceError("DeepSeek API 未返回有效文本结果")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIServiceError("DeepSeek API 返回结果不是有效 JSON") from exc
