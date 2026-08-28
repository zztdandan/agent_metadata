# 项目的安装与启动

当前项目一共需要三项内容的配置：
1. 后端backend目录
2. 前端frontend目录
3. 安装在当前环境中的hermes

## 安装并构建前端

### 安装依赖
```bash
export PROJECT_ROOT="${PROJECT_ROOT:-/填入你的路径/dedge-datacenter}"
export FRONTEND_ROOT="${FRONTEND_ROOT:-$PROJECT_ROOT/frontend}"

cd "$FRONTEND_ROOT"
bun install
```

### 构建前端产物
```bash
cd "$FRONTEND_ROOT"
bun run build
```

## 安装并启动后端

### 环境需求
1. 已安装uv，如果未安装则可执行`curl -LsSf https://astral.sh/uv/install.sh | sh`
2. 已安装python

### 安装依赖
```bash
# 需要当前目录切换到datacenter目录
cd /填入你的路径/dedge-datacenter-harness/dedge-datacenter
uv sync --project backend
```

### 启动后端
**注意**：启动后端前，需要先**构建前端**，否则没有可显示的前端页面。如果已经构建过了且没有前端改动，则不需要重复构建。
```bash
export PROJECT_ROOT="${PROJECT_ROOT:-/填入你的路径/dedge-datacenter}"
export BACKEND_ROOT="${BACKEND_ROOT:-$PROJECT_ROOT/backend}"
export BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export GRAFANA_URL="${GRAFANA_URL:-grafana的地址url}" # export GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"

cd "$PROJECT_ROOT"
uv run --project "$BACKEND_ROOT" \
  uvicorn dedge_datacenter_api.main:app \
  --app-dir "$BACKEND_ROOT/src" \
  --host "$BACKEND_HOST" \
  --port "$BACKEND_PORT"
```

### 启动hermes
默认启动在8642端口
```bash
# 先设置临时环境变量
export HERMES_HOME="/填入你的路径/dedge-datacenter/.hermes/"
hermes gateway
```
