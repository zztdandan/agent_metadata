# dedge-datacenter

dedge 数据中心 MVP 主工程仓库。

## 当前定位

本仓库承载：
- backend：FastAPI API、catalog/currentView、WS/notify、静态页面托管
- frontend：独立 Vue 工程，核心组件为 `AgentWorkbench`
- catalog：dashboard catalog 与 schema
- 部署态唯一 `HERMES_HOME`：`.hermes/`
- 项目外接 agent 业务记忆：`runtime/agent-memory/tsdb-memory.json`

不承载：
- Harness 外层设计文档
- 运行态 Hermes 会话、日志、缓存、私有 memory 等副产物

## 测试与运行命令

不要把所有地址和 root 绑成一个总入口。下面按“每件事单独编制”来写：项目自身一组、Hermes 一组、tmpdeploy 一组、Grafana 容器一组。改哪一类，就只改那一类前面的常量。

### 1. 项目自身启动与测试

#### 1.1 环境校验

```bash
export HARNESS_ROOT="${HARNESS_ROOT:-$(cd .. && pwd)}"

cd "$HARNESS_ROOT"
bash scripts/check-agent-env.sh
```

#### 1.2 构建前端产物

```bash
export PROJECT_ROOT="${PROJECT_ROOT:-/home/base/repo/dedge/dedge-datacenter-harness/dedge-datacenter}"
export FRONTEND_ROOT="${FRONTEND_ROOT:-$PROJECT_ROOT/frontend}"

cd "$FRONTEND_ROOT"
bun install
bun run build
```

说明：
- 前端是独立 Vue 工程
- 后端托管的是 `frontend/dist`
- 运行时不需要第二个常驻前端 dev server

#### 1.3 启动后端

```bash
export PROJECT_ROOT="${PROJECT_ROOT:-/home/base/repo/dedge/dedge-datacenter-harness/dedge-datacenter}"
export BACKEND_ROOT="${BACKEND_ROOT:-$PROJECT_ROOT/backend}"
export BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export GRAFANA_URL="${GRAFANA_URL:-http://127.0.0.1:3000}"

cd "$PROJECT_ROOT"
uv run --project "$BACKEND_ROOT" \
  uvicorn dedge_datacenter_api.main:app \
  --app-dir "$BACKEND_ROOT/src" \
  --host "$BACKEND_HOST" \
  --port "$BACKEND_PORT"
```

#### 1.4 后端聚焦测试

```bash
export PROJECT_ROOT="${PROJECT_ROOT:-/home/base/repo/dedge/dedge-datacenter-harness/dedge-datacenter}"
export BACKEND_ROOT="${BACKEND_ROOT:-$PROJECT_ROOT/backend}"

cd "$PROJECT_ROOT"
uv run --project "$BACKEND_ROOT" pytest \
  backend/tests/test_main.py \
  backend/tests/test_catalog_api.py \
  -q
```

#### 1.5 本地健康检查

```bash
export BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export BACKEND_BASE_URL="${BACKEND_BASE_URL:-http://$BACKEND_HOST:$BACKEND_PORT}"

curl -sS "$BACKEND_BASE_URL/api/health"
curl -sS "$BACKEND_BASE_URL/api/catalog"
```

#### 1.6 可选：前端开发模式

```bash
export PROJECT_ROOT="${PROJECT_ROOT:-/home/base/repo/dedge/dedge-datacenter-harness/dedge-datacenter}"
export FRONTEND_ROOT="${FRONTEND_ROOT:-$PROJECT_ROOT/frontend}"

cd "$FRONTEND_ROOT"
bun run dev --host 0.0.0.0 --port 5173
```

### 2. Hermes 本地测试指令

#### 2.1 启动交互式 Hermes

```bash
export PROJECT_ROOT="${PROJECT_ROOT:-/home/base/repo/dedge/dedge-datacenter-harness/dedge-datacenter}"
export HERMES_HOME="${HERMES_HOME:-$PROJECT_ROOT/.hermes}"

cd "$PROJECT_ROOT"
HERMES_HOME="$HERMES_HOME" hermes chat
```

#### 2.2 一次性 smoke test

```bash
export PROJECT_ROOT="${PROJECT_ROOT:-/home/base/repo/dedge/dedge-datacenter-harness/dedge-datacenter}"
export HERMES_HOME="${HERMES_HOME:-$PROJECT_ROOT/.hermes}"
export BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export BACKEND_BASE_URL="${BACKEND_BASE_URL:-http://$BACKEND_HOST:$BACKEND_PORT}"

cd "$PROJECT_ROOT"
HERMES_HOME="$HERMES_HOME" hermes chat -q \
  "检查当前 backend ${BACKEND_BASE_URL} 是否可用，只返回一句话结论。"
```

### 3. tmpdeploy / TSS 启动与测试

tmpdeploy 是直接启动的本地部署目录，不是容器。这里只给它自己的 root。

#### 3.1 tmpdeploy root

```bash
export TMPDEPLOY_ROOT="${TMPDEPLOY_ROOT:-/home/base/repo/dedge/dedge-ts-interface-harness/tmpdeploy}"
```

#### 3.2 启动 tmpdeploy：01 / 02 / 03 全流程

按当前 tmpdeploy 脚本约定，初始化/灌数应走 `01`、`02`、`03` 这三步，而不是只执行 `start-bg.sh`。

```bash
cd "$TMPDEPLOY_ROOT"
./scripts/01-start-singleserver.sh
./scripts/02-init-runtime.sh
./scripts/03-start-dual-feed.sh
```

#### 3.3 停止 tmpdeploy

```bash
cd "$TMPDEPLOY_ROOT"
./scripts/stop.sh
```

#### 3.4 重做一轮 tmpdeploy 初始化

```bash
cd "$TMPDEPLOY_ROOT"
./scripts/stop.sh || true
./scripts/01-start-singleserver.sh
./scripts/02-init-runtime.sh
./scripts/03-start-dual-feed.sh
```

#### 3.5 TSS 健康检查

```bash
export TSS_BASE_URL="${TSS_BASE_URL:-http://127.0.0.1:18081}"
export TSS_BASIC_AUTH="${TSS_BASIC_AUTH:-admin:admin123}"

curl --fail-with-body -sS -u "$TSS_BASIC_AUTH" \
  "$TSS_BASE_URL/api/v1/runtime/health"
```

#### 3.6 TSS long-query 留痕

```bash
cd "$TMPDEPLOY_ROOT"
./scripts/run-longquery-evidence.sh
```

#### 3.7 TSS 运行态与长查询条目检查

```bash
export TSS_BASE_URL="${TSS_BASE_URL:-http://127.0.0.1:18081}"
export TSS_BASIC_AUTH="${TSS_BASIC_AUTH:-admin:admin123}"

python3 - <<'PY'
import base64
import json
import os
import urllib.request

base = os.environ["TSS_BASE_URL"].rstrip("/")
auth = "Basic " + base64.b64encode(os.environ["TSS_BASIC_AUTH"].encode()).decode()
req = urllib.request.Request(
    base + "/api/v1/query-entry",
    headers={"Authorization": auth},
)
with urllib.request.urlopen(req) as response:
    payload = json.load(response)
print(json.dumps({"code": payload.get("code"), "entry_count": len(payload.get("data", []))}, ensure_ascii=False))
PY
```

### 4. Grafana / InfluxDB / TDengine 启动与测试

Grafana 这组是容器启动。当前 compose 文件可参考：

- `/home/base/repo/github-refactor/grafana-harness/deploy/docker-compose.yml`

这里只给 Grafana 这一组自己的 compose root。

#### 4.1 Grafana compose root

```bash
export GRAFANA_DEPLOY_DIR="${GRAFANA_DEPLOY_DIR:-/home/base/repo/github-refactor/grafana-harness/deploy}"
```

#### 4.2 启动 Grafana + InfluxDB + TDengine

```bash
cd "$GRAFANA_DEPLOY_DIR"
docker compose up -d
```

#### 4.3 停止 Grafana + InfluxDB + TDengine

```bash
cd "$GRAFANA_DEPLOY_DIR"
docker compose down
```

#### 4.4 查看容器状态

```bash
cd "$GRAFANA_DEPLOY_DIR"
docker compose ps
```

#### 4.5 Grafana 健康检查

```bash
export GRAFANA_BASE_URL="${GRAFANA_BASE_URL:-http://127.0.0.1:3000}"

curl -sS "$GRAFANA_BASE_URL/api/health"
docker inspect grafana --format '{{range .Config.Env}}{{println .}}{{end}}' \
  | grep '^GF_SECURITY_ALLOW_EMBEDDING='
```

#### 4.6 InfluxDB 健康检查

```bash
export INFLUXDB_BASE_URL="${INFLUXDB_BASE_URL:-http://127.0.0.1:8086}"

curl -sS "$INFLUXDB_BASE_URL/health"
```

#### 4.7 TDengine 端口/进程检查

```bash
export TDENGINE_PORT="${TDENGINE_PORT:-6030}"

ss -ltnp | grep ":$TDENGINE_PORT" || true
docker ps --filter name=tdengine
```

### 5. 一组常用联调顺序

```bash
# 1) 启动 Grafana 容器组
export GRAFANA_DEPLOY_DIR="${GRAFANA_DEPLOY_DIR:-/home/base/repo/github-refactor/grafana-harness/deploy}"
cd "$GRAFANA_DEPLOY_DIR" && docker compose up -d

# 2) 启动 tmpdeploy
export TMPDEPLOY_ROOT="${TMPDEPLOY_ROOT:-/home/base/repo/dedge/dedge-ts-interface-harness/tmpdeploy}"
cd "$TMPDEPLOY_ROOT" && \
  ./scripts/01-start-singleserver.sh && \
  ./scripts/03-start-dual-feed.sh

# 3) 构建并启动本项目
export PROJECT_ROOT="${PROJECT_ROOT:-/home/base/repo/dedge/dedge-datacenter-harness/dedge-datacenter}"
export FRONTEND_ROOT="${FRONTEND_ROOT:-$PROJECT_ROOT/frontend}"
export BACKEND_ROOT="${BACKEND_ROOT:-$PROJECT_ROOT/backend}"
export BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"

cd "$FRONTEND_ROOT" && bun install && bun run build
cd "$PROJECT_ROOT" && uv run --project "$BACKEND_ROOT" \
  uvicorn dedge_datacenter_api.main:app \
  --app-dir "$BACKEND_ROOT/src" \
  --host "$BACKEND_HOST" \
  --port "$BACKEND_PORT"
```

再开一个终端执行：

```bash
export PROJECT_ROOT="${PROJECT_ROOT:-/home/base/repo/dedge/dedge-datacenter-harness/dedge-datacenter}"
export HERMES_HOME="${HERMES_HOME:-$PROJECT_ROOT/.hermes}"

cd "$PROJECT_ROOT"
HERMES_HOME="$HERMES_HOME" hermes chat -q \
  "检查 catalog、backend、Grafana public dashboard 链路是否可用，并只返回结论。"
```

## Hermes 目录边界

- `.hermes/` 本身就是唯一工作 home
- `config.yaml`、`SOUL.md`、`skills/` 都直接位于 `.hermes/` 根目录
- 不再使用 `.hermes/profiles/dedge-orchestrator/` 这种嵌套 profile 结构
- 业务长期事实优先放入项目文件，而不是 Hermes 私有 memory

## 当前项目资产

- `.hermes/`：项目本地 Hermes home
- `backend/`：FastAPI 后端代码
- `frontend/`：独立 Vue 工程
- `catalog/`：catalog JSON 与 schema
- `runtime/agent-memory/tsdb-memory.json`：当前 MVP 的 agent 系统地址 / 认证定位 / datasource 外接 memory

## Git 说明

- 默认分支：`main`
- 远端：`https://gitlab-c7n.lgdxtech.com/lgdxtech-nc220130005/dedge-datacenter.git`
- `.gitignore` 已屏蔽 Hermes 运行态副产物，仅保留 root-level Hermes skeleton 与项目业务资产
