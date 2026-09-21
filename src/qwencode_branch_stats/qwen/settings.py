from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..models import ModelPricing, WarningMessage


def read_pricing(path: Path) -> tuple[dict[str, ModelPricing], list[WarningMessage]]:
    warnings: list[WarningMessage] = []
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            settings = json.load(handle)
    except FileNotFoundError:
        return {}, [WarningMessage("settings_missing", f"Qwen settings not found: {path}")]
    except (OSError, ValueError) as exc:
        return {}, [WarningMessage("settings_unreadable", f"Cannot read Qwen settings: {exc}")]

    raw_pricing = settings.get("modelPricing", {}) if isinstance(settings, dict) else {}
    if not isinstance(raw_pricing, dict):
        return {}, [WarningMessage("unknown_qwen_schema", "modelPricing is not an object")]
    result: dict[str, ModelPricing] = {}
    for model, raw in raw_pricing.items():
        if not isinstance(raw, dict):
            continue
        try:
            raw_cache = raw.get("cacheReadPerMillionTokens")
            result[str(model)] = ModelPricing(
                input_per_million=Decimal(str(raw["inputPerMillionTokens"])),
                output_per_million=Decimal(str(raw["outputPerMillionTokens"])),
                cache_read_per_million=(
                    Decimal(str(raw_cache)) if raw_cache is not None else None
                ),
            )
        except (KeyError, InvalidOperation, TypeError, ValueError):
            warnings.append(WarningMessage("pricing_invalid", f"Invalid pricing for model {model}"))
    return result, warnings

