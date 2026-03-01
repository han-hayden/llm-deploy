"""Service verifier — tests deployed inference service."""

import logging

import httpx

logger = logging.getLogger(__name__)


async def verify_endpoint(endpoint: str, model_name: str = "model", timeout: int = 60) -> dict:
    """Send a test inference request to verify the service is working.

    Returns verification result dict.
    """
    test_payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "hello"}],
        "max_tokens": 10,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(endpoint, json=test_payload)
            if resp.status_code == 200:
                return {
                    "status": "success",
                    "response_code": 200,
                    "response_time_ms": int(resp.elapsed.total_seconds() * 1000),
                    "response_body": resp.json(),
                }
            return {
                "status": "failed",
                "response_code": resp.status_code,
                "error": resp.text,
            }
    except httpx.TimeoutException:
        return {"status": "timeout", "error": "服务响应超时"}
    except httpx.ConnectError:
        return {"status": "unreachable", "error": "无法连接到服务"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
