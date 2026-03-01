"""Environment pre-checker — validates target environment before deployment."""

import logging

from llm_deploy.knowledge.loader import kb

logger = logging.getLogger(__name__)


async def run_precheck(
    hardware_model: str,
    engine_name: str,
    gpu_count_needed: int,
    connection_config: dict,
    env_type: str = "docker",
) -> dict:
    """Run environment pre-deployment checks.

    In production, this SSHs to the target and runs diagnostic commands.
    For now, returns simulated precheck results.
    """
    chip = kb.get_chip(hardware_model) or kb.find_chip(hardware_model)
    items = []

    # GPU/NPU device check
    vendor = chip.get("_vendor", "NVIDIA") if chip else "NVIDIA"
    if vendor == "NVIDIA":
        items.append(_check_item("GPU 设备检测", "pass",
                                 f"检测到 {gpu_count_needed}+ GPU",
                                 f"需要 {gpu_count_needed} 张", ""))
    else:
        items.append(_check_item("NPU 设备检测", "pass",
                                 f"检测到 {gpu_count_needed}+ NPU",
                                 f"需要 {gpu_count_needed} 张", ""))

    # Driver check
    if chip:
        drivers = chip.get("driver_versions", [])
        rec_driver = next((d for d in drivers if d.get("status") == "recommended"), drivers[0] if drivers else None)
        if rec_driver:
            items.append(_check_item("驱动版本", "pass",
                                     rec_driver.get("version", ""),
                                     f">= {rec_driver.get('version', '')}",
                                     ""))
            # SDK check
            sdk_key = "cann" if vendor == "Huawei_Ascend" else "cuda"
            sdk_ver = rec_driver.get(sdk_key, rec_driver.get("cuda", ""))
            if sdk_ver:
                items.append(_check_item(f"{sdk_key.upper()} 版本", "pass",
                                         sdk_ver, f"匹配 {engine_name}", ""))

    # Docker check
    if env_type == "docker":
        items.append(_check_item("Docker 版本", "pass", "24.0.7", ">= 20.10", ""))

    # Vendor runtime check
    if vendor == "Huawei_Ascend":
        items.append(_check_item("Ascend Runtime", "pass", "已安装", "已安装", ""))
    elif vendor == "NVIDIA":
        items.append(_check_item("NVIDIA Container Toolkit", "pass", "已安装", "已安装", ""))

    # Disk space check
    items.append(_check_item("磁盘空间", "pass", "剩余 500 GB", "需要 200 GB", ""))

    # Model weights check
    items.append(_check_item("模型权重", "pass", "已就位", "已就位", ""))

    all_pass = all(i["status"] == "pass" for i in items)
    return {
        "passed": all_pass,
        "items": items,
    }


def _check_item(name: str, status: str, actual: str, expected: str, message: str) -> dict:
    return {
        "name": name,
        "status": status,
        "actual": actual,
        "expected": expected,
        "message": message,
    }
