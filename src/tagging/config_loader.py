"""Config loader: merges `config/app.yaml` (common) with env-specific files.

Behavior:
- Reads `config/app.yaml` to determine `environment` (develop|production).
- Loads `config/<environment>/<environment>.yaml` and deep-merges keys, returning a dict.
- Supports environment variable interpolation with ${VAR} syntax.
"""
from pathlib import Path
from typing import Any, Dict
import os
import string

try:
    import yaml
except Exception as exc:  # pragma: no cover - user will install PyYAML
    raise ImportError("PyYAML is required: pip install PyYAML") from exc


def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Return deep-merged dict of a <- b (b overrides a)."""
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def interpolate_env_vars(data: Any) -> Any:
    """Recursively interpolate ${VAR} or ${VAR:default} placeholders with environment variables."""
    if isinstance(data, str):
        # Custom interpolation for ${VAR} or ${VAR:default}
        import re
        def replacer(match):
            var_expr = match.group(1)
            if ':' in var_expr:
                var, default = var_expr.split(':', 1)
                return os.environ.get(var, default)
            else:
                return os.environ.get(var_expr, '')
        return re.sub(r'\$\{([^}]+)\}', replacer, data)
    elif isinstance(data, dict):
        return {k: interpolate_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [interpolate_env_vars(item) for item in data]
    else:
        return data


def load_config(root: Path = Path("config")) -> Dict[str, Any]:
    app_path = root / "app.yaml"
    if not app_path.exists():
        raise FileNotFoundError(f"Missing {app_path}")
    with app_path.open(encoding="utf-8") as fh:
        app_cfg = yaml.safe_load(fh) or {}

    env = app_cfg.get("environment", "develop")
    env_path = root / env / f"{env}.yaml"
    env_cfg = {}
    if env_path.exists():
        with env_path.open(encoding="utf-8") as fh:
            env_cfg = yaml.safe_load(fh) or {}

    merged = deep_merge(app_cfg, env_cfg)
    interpolated = interpolate_env_vars(merged)
    return interpolated


if __name__ == "__main__":
    # quick CLI for debugging
    import json

    cfg = load_config(Path("config"))
    print(json.dumps(cfg, indent=2))
