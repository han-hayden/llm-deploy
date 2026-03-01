"""Dockerfile generator — renders Dockerfiles from Jinja2 templates."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def generate_dockerfile(
    engine_name: str,
    base_image: str,
    model_name: str,
    extra_pip_packages: list[str] | None = None,
    api_wrapper: bool = False,
    startup_command: str = "",
) -> str:
    """Generate a Dockerfile from template."""
    env = get_jinja_env()

    # Try engine-specific template, fall back to generic
    template_name = f"dockerfiles/{engine_name}.Dockerfile.j2"
    try:
        template = env.get_template(template_name)
    except Exception:
        template = env.get_template("dockerfiles/generic.Dockerfile.j2")

    return template.render(
        base_image=base_image,
        model_name=model_name,
        extra_pip_packages=extra_pip_packages or [],
        api_wrapper=api_wrapper,
        startup_command=startup_command,
    )


def generate_image_tag(model_name: str, engine_name: str, hardware_model: str) -> str:
    """Generate a Docker image tag."""
    from datetime import datetime
    date_str = datetime.now().strftime("%m%d")
    model_short = model_name.lower().replace("/", "-").replace("_", "-")
    return f"llm-deploy/{model_short}:{engine_name}-{hardware_model.lower()}-{date_str}"
