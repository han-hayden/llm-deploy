# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**LLM Deploy (大模型自助部署平台)** — A self-service platform for deploying large language models across heterogeneous hardware (NVIDIA + 5 domestic Chinese GPU vendors). Currently in the **requirements/design phase** with no implementation code yet.

Core PRD: `PRD_LLM_Deploy_大模型自助部署平台_v1.0.md`

## Architecture: Four-Journey Workflow

The entire product is structured around four sequential user operations:

1. **Model Adaptation Registration** — User inputs model name/HuggingFace/ModelScope link + hardware model (e.g., "Ascend 910B4 64G"). System parses `config.json`, README/Model Card, and queries hardware knowledge base to produce an adaptation task.
2. **Model Weight Download** — Download weights to local or remote environment from HuggingFace/ModelScope with resume and SHA256 verification.
3. **Inference Engine Image Generation** — Auto-query model official config + vendor adaptation docs → generate Docker image + startup commands + optional FastAPI OpenAI-compatible wrapper. Includes intelligent parameter calculation engine (TP/PP/max-model-len/dtype) with user-adjustable GPU count that triggers recalculation.
4. **Deployment & Launch** — Upload artifacts to target environment → pre-deployment checks (drivers, CUDA/CANN/DTK versions, disk) → deploy (Docker/K8s) → auto-verify with test inference request.

## Key Domain Concepts

- **Hardware Knowledge Base**: YAML/JSON store mapping hardware models → driver versions → SDK versions → inference frameworks → base images → container device paths → K8s resource declarations. Supports dynamic discovery from vendor websites for unknown hardware.
- **Parameter Calculation Engine**: Computes startup params from 4 sources: model `config.json`, Model Card recommendations, hardware specs, inference engine parameter schema. All params show calculation rationale.
- **Supported Hardware**: NVIDIA, Huawei Ascend (910B3/910B4/910C), Hygon DCU (K100_AI), MetaX (N260/C500/C550), Baidu Kunlun (R200/R300), Iluvatar (BI-150/MR-V100).
- **Supported Inference Engines**: vLLM, TGI, MindIE, LMDeploy, FastDeploy, IGIE, plus vendor-specific variants (vLLM-Ascend, vLLM-DCU, MACA-vLLM, IX-vLLM).

## Document Map

| File | Purpose |
|------|---------|
| `PRD_LLM_Deploy_大模型自助部署平台_v1.0.md` | Complete PRD with field specs, Mermaid flows, API definitions |
| `设计目标.md` | Concise design goals and external reference links |
| `系统需求提示词.md` | Prompt template for generating system architecture (SDD) |
| `用户需求提示词.md` | Prompt template for expanding user requirements |

## Language

All documentation is in **Chinese (Simplified)**. Code comments and commit messages should follow project convention once implementation begins.
