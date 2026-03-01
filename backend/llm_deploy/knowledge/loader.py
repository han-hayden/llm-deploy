"""YAML knowledge base loader — loads hardware and engine specs into memory."""

from pathlib import Path
from typing import Any

import yaml


class KnowledgeBase:
    """In-memory knowledge base loaded from YAML files."""

    def __init__(self):
        self._vendors: dict[str, dict] = {}  # vendor_key -> full vendor dict
        self._chips: dict[str, dict] = {}  # chip_model -> chip dict (with vendor info)
        self._engines: dict[str, dict] = {}  # engine_name -> engine dict

    def load(self, base_dir: str | Path | None = None) -> None:
        """Load all YAML files from the knowledge directory."""
        if base_dir is None:
            base_dir = Path(__file__).parent
        else:
            base_dir = Path(base_dir)

        # Load vendor files
        vendors_dir = base_dir / "vendors"
        if vendors_dir.exists():
            for yaml_file in sorted(vendors_dir.glob("*.yaml")):
                self._load_vendor(yaml_file)

        # Load engine files
        engines_dir = base_dir / "engines"
        if engines_dir.exists():
            for yaml_file in sorted(engines_dir.glob("*.yaml")):
                self._load_engine(yaml_file)

    def _load_vendor(self, path: Path) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        vendor_key = data["vendor"]
        self._vendors[vendor_key] = data
        for chip in data.get("chips", []):
            chip_key = chip["model"]
            chip["_vendor"] = vendor_key
            chip["_vendor_cn"] = data.get("vendor_cn", vendor_key)
            self._chips[chip_key] = chip

    def _load_engine(self, path: Path) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self._engines[data["engine"]] = data

    # --- Query interfaces ---

    def get_all_vendors(self) -> list[dict]:
        """Return list of vendor summaries."""
        results = []
        for vendor_key, vendor in self._vendors.items():
            results.append({
                "vendor": vendor_key,
                "vendor_cn": vendor.get("vendor_cn", vendor_key),
                "chip_count": len(vendor.get("chips", [])),
                "chips": [
                    {"model": c["model"], "display_name": c["display_name"],
                     "memory_gb": c["memory_gb"]}
                    for c in vendor.get("chips", [])
                ],
            })
        return results

    def get_all_chips(self) -> list[dict[str, Any]]:
        """Return flat list of all chips with vendor info."""
        results = []
        for model, chip in self._chips.items():
            results.append({
                "model": model,
                "display_name": chip["display_name"],
                "vendor": chip["_vendor"],
                "vendor_cn": chip["_vendor_cn"],
                "memory_gb": chip["memory_gb"],
                "memory_type": chip.get("memory_type", ""),
                "compute_tflops_fp16": chip.get("compute_tflops_fp16", 0),
                "bf16_support": chip.get("bf16_support", False),
                "interconnect": chip.get("interconnect", ""),
            })
        return results

    def get_chip(self, model: str) -> dict | None:
        """Get full chip info by model identifier."""
        return self._chips.get(model)

    def find_chip(self, query: str) -> dict | None:
        """Fuzzy find a chip by model string (case-insensitive, partial match)."""
        query_lower = query.lower().replace(" ", "").replace("-", "").replace("_", "")
        for model, chip in self._chips.items():
            model_norm = model.lower().replace(" ", "").replace("-", "").replace("_", "")
            display_norm = chip["display_name"].lower().replace(" ", "").replace("-", "").replace("_", "")
            if query_lower in model_norm or query_lower in display_norm or model_norm in query_lower:
                return chip
        return None

    def get_compatible_engines(self, chip_model: str) -> list[dict]:
        """Get engines compatible with a specific chip."""
        chip = self._chips.get(chip_model)
        if not chip:
            return []
        return chip.get("compatible_engines", [])

    def get_recommended_engine(self, chip_model: str) -> dict | None:
        """Get the first (recommended) engine for a chip."""
        engines = self.get_compatible_engines(chip_model)
        return engines[0] if engines else None

    def get_engine(self, engine_name: str) -> dict | None:
        """Get engine spec by name."""
        return self._engines.get(engine_name)

    def get_container_config(self, chip_model: str) -> dict | None:
        """Get container configuration for a chip."""
        chip = self._chips.get(chip_model)
        if not chip:
            return None
        return chip.get("container_config")

    def get_chip_driver_info(self, chip_model: str) -> list[dict]:
        """Get driver version info for a chip."""
        chip = self._chips.get(chip_model)
        if not chip:
            return []
        return chip.get("driver_versions", [])


# Global singleton
kb = KnowledgeBase()
