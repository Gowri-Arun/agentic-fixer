from pathlib import Path

import yaml

from app.evaluation.models import EvaluationConfig, SiteConfig


class ConfigError(Exception):
    """Raised when configuration is invalid."""


def load_config(path: Path) -> EvaluationConfig:
    """Load and validate an evaluation configuration YAML file."""
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")

    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML syntax: {exc}") from exc

    if not isinstance(raw, dict) or "sites" not in raw:
        raise ConfigError("Configuration must contain a 'sites' key")

    raw_sites = raw["sites"]
    if not isinstance(raw_sites, list):
        raise ConfigError("'sites' must be a list")

    sites: list[SiteConfig] = []
    seen_urls: set[str] = set()

    for index, raw_site in enumerate(raw_sites):
        try:
            site = SiteConfig(**raw_site)
        except Exception as exc:
            raise ConfigError(f"Site at index {index} is invalid: {exc}") from exc

        url_str = str(site.url)
        if url_str in seen_urls:
            raise ConfigError(f"Duplicate URL at index {index}: {url_str}")
        seen_urls.add(url_str)

        sites.append(site)

    return EvaluationConfig(sites=sites)
