# Plan: LLM Deploy 大模型自助部署平台 — 全栈开发计划

## Context

项目当前状态：**仅有设计文档，无任何代码**。需从零搭建完整工程，实现四旅程主流程，推送至 GitHub。

- 输入文档：`PRD_LLM_Deploy_v1.0.md` / `SDD_LLM_Deploy_v1.0.md` / `交互原型_LLM_Deploy_v1.0.md`
- 远程仓库：`https://github.com/han-hayden/llm-deploy`
- 安全要求：**禁止提交** `.env`、密码、密钥、kubeconfig 等敏感信息

## Git 策略

- 每个 Phase 完成后执行 `git commit + git push`
- commit message 格式：`phase-X: 简要描述`
- `.gitignore` 首次提交即包含完整规则（__pycache__、.env、*.sqlite、node_modules 等）
- 设计文档（PRD/SDD/交互原型/提示词）放入 `docs/` 目录纳入版本管理
- `interact-pngs/` 图片文件体积大，加入 `.gitignore` 不上传

---

## Phase 0: 项目初始化与工程骨架

**目标**：git 初始化、目录结构、依赖声明、CI 基础，可 `pip install -e .` 并 `uvicorn` 启动空服务

**文件清单**：
```
llm-deploy/
├── .gitignore
├── pyproject.toml              # Python 包定义 + 依赖 (FastAPI, SQLAlchemy, Alembic, Paramiko, httpx, cachetools, Jinja2, pyyaml, uvicorn)
├── README.md                   # 项目简介 + 本地开发指南
├── CLAUDE.md                   # 迁移已有版本
├── docs/                       # 设计文档归档
│   ├── PRD_LLM_Deploy_v1.0.md
│   ├── SDD_LLM_Deploy_v1.0.md
│   ├── 交互原型_LLM_Deploy_v1.0.md
│   ├── 设计目标.md
│   ├── 系统需求提示词.md
│   └── 用户需求提示词.md
├── backend/
│   ├── llm_deploy/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app factory + lifespan
│   │   ├── config.py           # pydantic-settings: DB_URL, UPLOAD_DIR, LOG_LEVEL 等
│   │   └── database.py         # SQLAlchemy engine + sessionmaker + Base
│   ├── alembic/
│   │   ├── alembic.ini
│   │   └── env.py
│   └── tests/
│       └── __init__.py
└── frontend/                   # 空目录占位，Phase 6 填充
    └── .gitkeep
```

**验证**：`pip install -e . && uvicorn llm_deploy.main:app --reload` 启动后访问 `/docs` 看到 Swagger UI

**Git commit**：`phase-0: project skeleton with FastAPI + SQLAlchemy + Alembic`

---

## Phase 1: 数据模型 + 硬件知识库 + YAML 加载

**目标**：定义全部 ORM 模型，创建数据库迁移，实现 YAML 知识库加载器

**文件清单**：
```
backend/llm_deploy/
├── models/
│   ├── __init__.py
│   ├── task.py                 # AdaptationTask (主实体，含 status 状态机)
│   ├── model_metadata.py       # ModelMetadata (config.json + Model Card 解析结果)
│   ├── download.py             # DownloadTask
│   ├── image_build.py          # ImageBuildTask + ParamCalculation
│   ├── deployment.py           # Deployment
│   └── environment.py          # Environment
├── knowledge/
│   ├── __init__.py
│   ├── loader.py               # YAML 加载器：启动时加载到内存，提供查询接口
│   ├── vendors/
│   │   ├── nvidia.yaml
│   │   └── huawei_ascend.yaml  # 先实现 2 个代表性厂商
│   └── engines/
│       └── vllm.yaml           # 先实现 vLLM 引擎
alembic/
└── versions/
    └── 001_initial_schema.py   # 首次迁移
tests/
├── test_models.py              # ORM 模型基础 CRUD
└── test_knowledge_loader.py    # YAML 加载 + 查询
```

**关键实体字段** (源自 SDD ER 图)：
- `AdaptationTask`: id, task_name(UK), model_identifier, model_source, hardware_model, engine, dtype, status(enum), anomaly_flags(JSON)
- `ModelMetadata`: task_id(FK), model_name, architectures, param_count, hidden_size, num_layers, num_heads, num_kv_heads, vocab_size, max_position_embeddings, torch_dtype, quantization_config(JSON), model_card_parsed(JSON), weight_files(JSON)
- `DownloadTask`: task_id(FK), source, target_type, target_env_id, storage_path, total_size, downloaded_size, status, speed, eta
- `ImageBuildTask`: task_id(FK), engine_name, engine_version, base_image, dockerfile_content, startup_command, image_tag, api_wrapper_injected, status, build_log
- `ParamCalculation`: task_id(FK), gpu_count, dtype, tp, pp, max_model_len, max_num_seqs, gpu_mem_util, enforce_eager, all_params(JSON), rationale(JSON), memory_allocation(JSON)
- `Deployment`: task_id(FK), environment_id(FK), deploy_mode, status, precheck_report(JSON), api_endpoint, deploy_config(JSON), verification_result(JSON)
- `Environment`: id, name(UK), env_type, connection_type, connection_config(JSON), hardware_info(JSON)

**验证**：`alembic upgrade head` 创建表 → `pytest tests/test_models.py tests/test_knowledge_loader.py`

**Git commit**：`phase-1: ORM models, Alembic migration, YAML knowledge base loader`

---

## Phase 2: 旅程一 — 模型适配登记 (后端 API + 服务层)

**目标**：实现模型解析（config.json + Model Card）、硬件匹配、适配方案生成

**文件清单**：
```
backend/llm_deploy/
├── api/
│   ├── __init__.py
│   ├── deps.py                 # 公共依赖 (get_db session)
│   ├── tasks.py                # POST /api/v1/tasks, GET /api/v1/tasks/{id}, GET /api/v1/tasks
│   └── models.py               # POST /api/v1/models/parse
├── schemas/
│   ├── __init__.py
│   ├── task.py                 # Pydantic request/response schemas
│   └── model.py
├── services/
│   ├── __init__.py
│   ├── task_manager.py         # 任务创建 + 状态机转换
│   ├── model_parser.py         # 解析 HuggingFace/ModelScope 的 config.json + README
│   └── hardware_matcher.py     # 匹配 YAML 知识库中的硬件 + 推荐引擎
├── adapters/
│   ├── __init__.py
│   ├── huggingface.py          # HuggingFace Hub API 调用 (httpx)
│   └── modelscope_adapter.py   # ModelScope API 调用
tests/
├── test_api_tasks.py
├── test_model_parser.py
└── test_hardware_matcher.py
```

**核心逻辑**：
1. 用户提交 model_identifier + hardware_model → 创建 AdaptationTask (status=created)
2. 解析 model_identifier → 判断来源 (HuggingFace/ModelScope/名称)
3. 拉取 config.json → 提取 model_type, param_count, hidden_size 等
4. 拉取 README/Model Card → 提取推荐框架、启动命令、VRAM 需求
5. 查询 YAML 知识库 → 匹配硬件型号 → 推荐 engine + dtype
6. 生成异常标记 (anomaly_flags)：如模型过大、硬件不支持某 dtype
7. 保存 ModelMetadata → 更新 task status=parsed

**验证**：`curl -X POST /api/v1/tasks -d '{"model_identifier":"Qwen/Qwen2-7B","hardware_model":"910B4"}'` 返回完整解析结果

**Git commit**：`phase-2: journey-1 model parsing, hardware matching, task API`

---

## Phase 3: 旅程二 — 模型权重下载 (后端)

**目标**：实现后台异步下载、断点续传、SHA256 校验、进度上报

**文件清单**：
```
backend/llm_deploy/
├── api/
│   └── downloads.py            # POST /api/v1/models/download, GET /api/v1/models/download/{id}
├── schemas/
│   └── download.py
├── services/
│   └── download_manager.py     # 调用 huggingface_hub / modelscope SDK 下载，支持断点续传
├── bg_tasks/
│   ├── __init__.py
│   ├── worker.py               # ThreadPoolExecutor 管理 (submit/cancel/status)
│   └── tasks.py                # download_task: 执行下载 + 进度更新到 DB
tests/
├── test_download_api.py
└── test_worker.py
```

**核心逻辑**：
1. 用户选择下载源 (HuggingFace/ModelScope) + 目标 (本地路径 / 远程环境)
2. 提交下载到 ThreadPoolExecutor → 返回 download_id
3. 后台线程执行：逐文件下载，更新 downloaded_size/speed/eta 到 DB
4. 支持断点续传：检测已下载文件 + 大小，跳过已完成
5. 下载完成后 SHA256 校验
6. SSE 或轮询接口返回实时进度

**验证**：启动下载任务 → 轮询进度 API 看到 0%→100% → 文件完整性校验通过

**Git commit**：`phase-3: journey-2 model weight download with resume and progress`

---

## Phase 4: 旅程三 — 推理引擎镜像生成 (后端)

**目标**：参数计算引擎 + Dockerfile 生成 + 镜像构建 + OpenAI API wrapper 注入

**文件清单**：
```
backend/llm_deploy/
├── api/
│   ├── params.py               # POST /api/v1/params/calculate, PUT /api/v1/params/calculate
│   └── images.py               # POST /api/v1/images/build, GET /api/v1/images/build/{id}
├── schemas/
│   ├── params.py
│   └── image.py
├── services/
│   ├── param_calculator.py     # 核心：TP/PP/max_model_len/dtype 计算 + rationale
│   ├── dockerfile_generator.py # Jinja2 模板渲染 Dockerfile
│   ├── command_builder.py      # 启动命令构建（引擎参数映射）
│   ├── image_builder.py        # subprocess docker build + 日志流
│   └── api_wrapper.py          # FastAPI OpenAI 兼容 wrapper 代码注入判断
├── adapters/
│   └── container/
│       ├── __init__.py
│       ├── base.py             # ContainerAdapter Protocol
│       ├── nvidia.py
│       └── ascend.py           # 先实现 2 个
├── templates/
│   ├── dockerfiles/
│   │   ├── vllm.Dockerfile.j2
│   │   └── mindie.Dockerfile.j2
│   ├── startup_commands/
│   │   ├── vllm.sh.j2
│   │   └── mindie.sh.j2
│   └── api_wrappers/
│       └── openai_wrapper.py.j2   # FastAPI OpenAI 兼容 wrapper 模板
tests/
├── test_param_calculator.py    # 关键：测试计算正确性
├── test_dockerfile_generator.py
└── test_command_builder.py
```

**参数计算引擎核心算法** (源自 SDD §4.3)：
1. 确定 dtype → 检查硬件支持 → 必要时降级
2. weight_memory = param_count × bytes_per_dtype
3. min_cards = ceil(weight_memory / (card_memory × 0.9))
4. tensor_parallel = min(valid_tp where tp ≥ min_cards and num_heads % tp == 0)
5. available_memory → max_kv_memory → max_model_len
6. 合并 Model Card 推荐值
7. 每个参数附带 rationale 说明计算过程
8. 用户修改 gpu_count → 联动重算全部参数

**验证**：
- `POST /api/v1/params/calculate` 输入 Qwen2-7B + 910B4 → 返回 tp=1, max_model_len 等 + rationale
- `PUT /api/v1/params/calculate` 修改 gpu_count=2 → 重算返回新值
- `POST /api/v1/images/build` → 构建 Docker 镜像 → 查询日志

**Git commit**：`phase-4: journey-3 param calculator, Dockerfile generator, image builder`

---

## Phase 5: 旅程四 — 部署与启动 (后端)

**目标**：环境管理、环境预检、Docker/K8s 部署、服务验证

**文件清单**：
```
backend/llm_deploy/
├── api/
│   ├── environments.py         # CRUD /api/v1/environments
│   ├── deployments.py          # POST /api/v1/deployments, GET status, POST verify
│   └── hardware.py             # GET /api/v1/hardware/compatibility
├── schemas/
│   ├── environment.py
│   ├── deployment.py
│   └── hardware.py
├── services/
│   ├── env_prechecker.py       # SSH 连接 → 检查 GPU/驱动/CUDA/磁盘
│   ├── deployer.py             # Docker run / kubectl apply 执行部署
│   └── service_verifier.py     # 发送测试推理请求验证服务可用
├── adapters/
│   ├── ssh_executor.py         # Paramiko SSH 命令执行
│   └── container/
│       ├── hygon.py            # 补充更多厂商
│       ├── metax.py
│       ├── kunlunxin.py
│       └── iluvatar.py
├── templates/
│   └── k8s_manifests/
│       ├── deployment.yaml.j2
│       └── service.yaml.j2
tests/
├── test_env_prechecker.py
├── test_deployer.py
└── test_environments_api.py
```

**核心逻辑**：
1. 环境注册：SSH 连接信息 / kubeconfig（存 DB，v1.0 明文，.gitignore 排除 DB 文件）
2. 预检：SSH 到目标 → 执行 nvidia-smi/npu-smi → 检查驱动版本 → 检查磁盘空间 → 生成报告
3. 部署：
   - Docker: `docker load` + `docker run` (通过 ContainerAdapter 获取 device_args/env_vars/volumes)
   - K8s: 渲染 YAML 模板 → `kubectl apply`
4. 验证：等待服务就绪 → 发送 `POST /v1/chat/completions` 测试请求 → 记录首次响应延迟

**验证**：注册环境 → 预检通过 → 部署 → 自动验证 → 返回 API endpoint

**Git commit**：`phase-5: journey-4 environment precheck, deployment, service verification`

---

## Phase 6: 前端 — React + Ant Design 全页面实现

**目标**：实现交互原型定义的全部页面，对接后端 API

**文件清单**：
```
frontend/
├── package.json                # react, react-dom, antd, @ant-design/pro-components,
│                               # @ant-design/charts, axios, react-router-dom, typescript
├── tsconfig.json
├── vite.config.ts
├── index.html
├── src/
│   ├── main.tsx                # 入口
│   ├── App.tsx                 # 路由 + Layout
│   ├── api/
│   │   └── client.ts           # axios instance + API 函数封装
│   ├── layouts/
│   │   └── MainLayout.tsx      # 左侧边栏 + 右侧内容区
│   ├── pages/
│   │   ├── Overview.tsx                    # 总览：快捷入口卡片 + 统计 + 最近任务
│   │   ├── tasks/
│   │   │   ├── TaskList.tsx                # 任务列表 + 筛选
│   │   │   ├── TaskCreate.tsx              # 新建适配任务表单 (旅程一入口)
│   │   │   └── TaskDetail.tsx              # 任务详情：四旅程 Step 导航
│   │   ├── environments/
│   │   │   └── EnvironmentList.tsx         # 环境管理 + 注册弹窗
│   │   └── hardware/
│   │       ├── HardwareOverview.tsx        # 厂商卡片网格
│   │       └── HardwareDetail.tsx          # 芯片详情 + 兼容引擎
│   ├── components/
│   │   ├── JourneySteps.tsx               # 四旅程步骤条
│   │   ├── journey/
│   │   │   ├── J1AdaptationResult.tsx     # 旅程一：解析结果展示
│   │   │   ├── J2Download.tsx             # 旅程二：下载进度
│   │   │   ├── J3ParamAndBuild.tsx        # 旅程三：参数表 + 构建日志
│   │   │   └── J4Deploy.tsx               # 旅程四：预检 + 部署 + 验证
│   │   ├── TerminalLog.tsx                # 终端日志组件 (黑底白字)
│   │   ├── MemoryChart.tsx                # 显存分配柱状图
│   │   └── PrecheckReport.tsx             # 预检报告组件
│   └── types/
│       └── index.ts                       # TypeScript 类型定义 (与后端 schema 对齐)
```

**页面 → 后端 API 映射**：
| 页面 | 调用 API |
|------|----------|
| Overview | `GET /api/v1/tasks` (recent) |
| TaskList | `GET /api/v1/tasks` + filters |
| TaskCreate | `POST /api/v1/tasks` |
| TaskDetail/J1 | `GET /api/v1/tasks/{id}` |
| TaskDetail/J2 | `POST /api/v1/models/download` + `GET /api/v1/models/download/{id}` (轮询) |
| TaskDetail/J3 | `POST /api/v1/params/calculate` + `PUT recalculate` + `POST /api/v1/images/build` + `GET build/{id}` |
| TaskDetail/J4 | `POST /api/v1/deployments` + `GET status` + `POST verify` |
| EnvironmentList | `CRUD /api/v1/environments` |
| Hardware | `GET /api/v1/hardware/compatibility` |

**验证**：`npm run dev` → 浏览器访问 → 走通新建任务 → 查看详情 → 四旅程页面均可渲染

**Git commit**：`phase-6: frontend React app with all pages and API integration`

---

## Phase 7: 联调 + Docker Compose 整合

**目标**：前后端联调，提供 docker-compose 一键启动

**文件清单**：
```
├── docker-compose.yml          # backend + frontend(nginx) + postgres(可选)
├── backend/Dockerfile
├── frontend/Dockerfile         # multi-stage: build → nginx serve
├── frontend/nginx.conf         # 反向代理 /api → backend
├── .env.example                # 环境变量模板 (不含真实值)
```

**验证**：`docker-compose up` → 浏览器访问前端 → 完整走通四旅程

**Git commit**：`phase-7: docker-compose integration with frontend and backend`

---

## 安全红线 (.gitignore 必须包含)

```gitignore
# Sensitive
.env
*.sqlite
*.db
kubeconfig*
**/id_rsa*
**/*.pem
**/*.key

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# Node
node_modules/
dist/
.vite/

# IDE
.idea/
.vscode/
*.swp

# Project specific
interact-pngs/
uploads/
models_cache/
```

## Verification (端到端测试路径)

1. `docker-compose up` 或本地分别启动 backend + frontend
2. 浏览器打开总览页 → 点击"新建任务"
3. 输入 `Qwen/Qwen2-7B` + 选择 `NVIDIA A100` → 提交 → 看到解析结果 (旅程一)
4. 点击"开始下载" → 进度条推进 (旅程二)
5. 查看参数计算结果 → 修改 GPU 数量 → 参数联动重算 → 构建镜像 (旅程三)
6. 选择环境 → 预检 → 部署 → 验证成功 (旅程四)
