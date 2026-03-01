"""ModelScope adapter — fetch model config and metadata."""

import re
import logging

import httpx

from llm_deploy.config import settings

logger = logging.getLogger(__name__)

MS_API_BASE = "https://modelscope.cn/api/v1/models"
MS_RAW_BASE = "https://modelscope.cn"


def _build_headers() -> dict:
    headers = {}
    if settings.MS_TOKEN:
        headers["Authorization"] = f"Bearer {settings.MS_TOKEN}"
    return headers


async def fetch_model_info(repo_id: str) -> dict | None:
    """Fetch model info from ModelScope API."""
    url = f"{MS_API_BASE}/{repo_id}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=_build_headers())
            if resp.status_code == 200:
                data = resp.json()
                return data.get("Data", data)
    except httpx.HTTPError as e:
        logger.error("ModelScope API error: %s", e)
    return None


async def fetch_config_json(repo_id: str) -> dict | None:
    """Fetch config.json from ModelScope repo."""
    url = f"{MS_RAW_BASE}/models/{repo_id}/resolve/master/config.json"
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers=_build_headers())
            if resp.status_code == 200:
                return resp.json()
    except httpx.HTTPError as e:
        logger.error("ModelScope config.json fetch error: %s", e)
    return None


async def fetch_readme(repo_id: str) -> str | None:
    """Fetch README.md from ModelScope repo."""
    url = f"{MS_RAW_BASE}/models/{repo_id}/resolve/master/README.md"
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers=_build_headers())
            if resp.status_code == 200:
                return resp.text
    except httpx.HTTPError as e:
        logger.error("ModelScope README fetch error: %s", e)
    return None


def parse_repo_id(identifier: str) -> str | None:
    """Extract repo_id from a ModelScope URL or name."""
    match = re.match(r"https?://modelscope\.cn/models/([^/]+/[^/]+?)(?:/.*)?$", identifier)
    if match:
        return match.group(1)
    return None
