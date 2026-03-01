"""HuggingFace Hub adapter — fetch model config and metadata via API."""

import re
import logging

import httpx

from llm_deploy.config import settings

logger = logging.getLogger(__name__)

HF_API_BASE = "https://huggingface.co/api/models"
HF_RAW_BASE = "https://huggingface.co"


def _build_headers() -> dict:
    headers = {}
    if settings.HF_TOKEN:
        headers["Authorization"] = f"Bearer {settings.HF_TOKEN}"
    return headers


def _get_base_url() -> str:
    if settings.HF_MIRROR:
        return settings.HF_MIRROR
    return HF_API_BASE


async def fetch_model_info(repo_id: str) -> dict | None:
    """Fetch model info from HuggingFace API."""
    url = f"{_get_base_url()}/{repo_id}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=_build_headers())
            if resp.status_code == 200:
                return resp.json()
            logger.warning("HF API returned %d for %s", resp.status_code, repo_id)
    except httpx.HTTPError as e:
        logger.error("HF API error: %s", e)
    return None


async def fetch_config_json(repo_id: str) -> dict | None:
    """Fetch config.json from HuggingFace repo."""
    base = settings.HF_MIRROR.rstrip("/") if settings.HF_MIRROR else HF_RAW_BASE
    url = f"{base}/{repo_id}/resolve/main/config.json"
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers=_build_headers())
            if resp.status_code == 200:
                return resp.json()
    except httpx.HTTPError as e:
        logger.error("HF config.json fetch error: %s", e)
    return None


async def fetch_readme(repo_id: str) -> str | None:
    """Fetch README.md from HuggingFace repo."""
    base = settings.HF_MIRROR.rstrip("/") if settings.HF_MIRROR else HF_RAW_BASE
    url = f"{base}/{repo_id}/resolve/main/README.md"
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers=_build_headers())
            if resp.status_code == 200:
                return resp.text
    except httpx.HTTPError as e:
        logger.error("HF README fetch error: %s", e)
    return None


def parse_repo_id(identifier: str) -> str | None:
    """Extract repo_id from a HuggingFace URL or name.

    Accepts:
    - "Qwen/Qwen2-7B"
    - "https://huggingface.co/Qwen/Qwen2-7B"
    - "https://hf-mirror.com/Qwen/Qwen2-7B"
    """
    # URL pattern
    match = re.match(r"https?://[^/]+/([^/]+/[^/]+?)(?:/.*)?$", identifier)
    if match:
        return match.group(1)
    # Direct repo_id pattern (org/model)
    if "/" in identifier and not identifier.startswith("http"):
        return identifier.strip()
    return None
