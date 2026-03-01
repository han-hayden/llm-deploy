# LLM Deploy — 大模型自助部署平台

自助式大模型部署平台，支持 NVIDIA 及国产 GPU（昇腾、海光、沐曦、昆仑芯、天数智芯），覆盖从模型解析、权重下载、镜像构建到部署验证的全流程。

## 四旅程工作流

1. **模型适配登记** — 输入模型名称/链接 + 硬件型号，自动解析模型配置并匹配硬件
2. **模型权重下载** — 从 HuggingFace/ModelScope 下载权重，支持断点续传和 SHA256 校验
3. **推理引擎镜像生成** — 自动计算启动参数（TP/PP/max-model-len），生成 Docker 镜像
4. **部署与启动** — 环境预检、Docker/K8s 部署、自动验证服务可用性

## 本地开发

### 后端

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[dev]"

# 数据库迁移
cd backend && alembic upgrade head && cd ..

# 启动后端
uvicorn llm_deploy.main:app --reload --app-dir backend

# 运行测试
pytest
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### Docker Compose

```bash
cp .env.example .env
docker-compose up
```

## 技术栈

- **后端**: Python 3.10+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **前端**: React 18, TypeScript, Ant Design 5, Vite
- **数据库**: SQLite (开发) / PostgreSQL (生产)
