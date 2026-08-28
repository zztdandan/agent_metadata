---
name: datacenter-agent-grafana-dashboard
description: 通过 Grafana MCP 为 dedge 构建与修改看板，使用 Infinity + TSS longstmt，并保持 catalog/currentView 与薄前端刷新闭环同步。
---

# dedge Grafana 看板

当任务涉及创建、修改或核验 Grafana 看板/面板时，使用本技能。

## 角色边界

1. Grafana 看板的创建/修改由 Agent + Grafana MCP 负责；直接 REST API 仅作为兜底。
2. backend 不负责管理 Grafana 看板；它只负责保存 catalog/currentView，并发送刷新信号。
3. frontend 只负责展示 iframe 页面与目录状态，不是看板编辑器。

## MCP 不可用时的兜底

如果 Grafana MCP 返回 401，或报“连续 3 次失败后不可达”，则改用 `.env` 中 service account token 走直接 REST API：

```bash
TOKEN=$(grep GRAFANA_SERVICE_ACCOUNT_TOKEN .hermes/.env | cut -d= -f2)
# 获取 dashboard
curl -s -H "Authorization: Bearer ***" {agentmemory.grafana.url}/api/dashboards/uid/<uid>
# 覆盖写回 dashboard
curl -s -X POST -H "Authorization: Bearer ***" -H "Content-Type: application/json" \
  -d '{"dashboard":{...},"overwrite":true,"message":"..."}' \
  {agentmemory.grafana.url}/api/dashboards/db
```

## 看板更新易错点：不要使用过期 JSON

**每次修改前，都必须先重新从 Grafana 拉取最新 dashboard JSON。** 不要复用本地缓存的旧副本。因为同一会话前一步改动可能已经改变了看板结构（例如把面板类型从 stat 改为 timeseries），旧副本会在你下一次写回时悄悄把这些改动覆盖掉。

正确的多次修改循环：
1. `GET /api/dashboards/uid/<uid>` 拿当前 JSON
2. 在最新 JSON 上修改
3. 用 `POST /api/dashboards/db` 且 `overwrite: true` 写回

## Infinity POST 面板 URL 必须带前导斜杠

Infinity 数据源的 panel target `url` 字段如果使用相对路径，**必须以 `/` 开头**：
- 正确：`"/api/v1/query/f2aa524146090be7"`
- 错误：`"api/v1/query/f2aa524146090be7"`

不带前导 `/` 时，Infinity 会错误拼接路径，请求实际不会发出（`responseCodeFromServer: 0`），面板显示无数据。这个症状很容易被误判为"Infinity backend handler 不支持 POST"或"公开看板渲染路径问题"——实际上只是 URL 格式错误。

**排查规则**：如果 ds/query API 返回 `responseCodeFromServer: 0` 且 `error: ""`，先检查：
1. URL 是否以 `/` 开头
2. target 是否有 `"source": "url"` 字段——这是 Infinity 发 HTTP 请求的开关，缺失则不发请求
3. `url_options` 是否包含完整的空字段（`body_form:[]`, `params:[]`, `headers:[]`, `body_graphql_query:""`, `body_graphql_variables:""`, `global_query_id:""`）

不要怀疑插件能力，Infinity backend handler 支持 POST。

## 面板类型转换检查表

当需要把面板类型从一种改成另一种（例如 stat → timeseries）时，不要只改 `type`，而应整体替换该 panel 的关键结构：
- `type`：新的面板类型
- `targets`：与新类型匹配的查询结构
- `fieldConfig.defaults.custom`：如 `drawStyle`、`lineWidth`、`fillOpacity`
- `options`：如 `tooltip`、`legend`
- `gridPos.h`：例如 timeseries 且带 legend 时，通常需要 `h:20+`

## 默认创建约束

1. **默认时间范围固定为最近 5 分钟**（`now-5m` 到 `now`），除非用户明确要求更长窗口。
2. **默认不要直接拉全量原始点**。如果用户没有指定采样策略，优先在 TSS/SQL 层做时间桶平均，让整段时间窗约为 30 个点。
3. 默认采样可按这个经验值落地：
   - `5m` → `10s` 平均（约 30 点）
   - `15m` → `30s` 平均（约 30 点）
   - 更长窗口 → 继续按“总点数约 30”反推 bucket/avg 窗口
4. 只有用户明确要求“看全量明细/不做平均”时，才切到全量点查询。

## Infinity 多序列：首选单 target + transforms

优先使用 **一个 target**，配合三段 Grafana transform 链。这样所有 prop 共用一次 API 调用；TSS 会缓存整模型响应，然后由面板侧 transforms 拆分成多条序列。

### transform 链：`filterByValue → partitionByValues → prepareTimeSeries`

```json
"targets": [{
  "format": "table",
  "columns": [
    {"selector": "_time", "text": "Time", "type": "timestamp"},
    {"selector": "_value", "text": "Value", "type": "number"},
    {"selector": "prop", "text": "Prop", "type": "string"}
  ],
  "url": "/api/v1/query/<fullModelLongstmtUri>",
  "url_options": {"data": "<identical body, no prop filter>"}
}],
"transformations": [
  {"id": "filterByValue", "options": {
    "filters": [{"fieldName": "Prop", "config": {"id": "regex", "options": {"value": "^CUR[0-9]+$"}}}],
    "type": "include", "match": "any"
  }},
  {"id": "partitionByValues", "options": {"fields": ["Prop"]}},
  {"id": "prepareTimeSeries", "options": {"multiFrameAsMany": true, "convertToMulti": "many"}}
]
```

为什么这样可行：
- `partitionByValues` 会先按 `Prop` 的不同值，把一张表拆成多张 frame
- `prepareTimeSeries` 再把每一张 frame 单独转换为时间序列
- 仅靠 `prepareTimeSeries` 无法按字符串列自动拆分，因此 `partitionByValues` 是必须步骤

**常见失败**：省略 `partitionByValues` 时，容易报：`Data is missing a number field`。

### target 期望的数据结构

这里的 target 应消费 **全模型 longstmt** 返回的 TypeFrame 行表；dashboard 侧只关心数据结构，不负责定义 longstmt 创建流程。面板应假定返回行至少包含：

- `_time`：时间戳
- `_value`：数值
- `prop`：测点名/序列名

longstmt 的创建方式、CLI 命令与缓存命中技巧，统一参考 `datacenter-agent-cloud-tss-query`。

### 多 target 兜底方案（仍有效）

如果 transforms 表现异常，可以退回按 prop 分 target 的方式（`dadevice-coll-1-monitor` 已验证过）。每个 target 通过 `url_options.data` 里的 `args.prop` 指定一个 prop，并把 value 列的 `text` 作为序列名。

## Infinity 单值 stat 面板模式

单值卡片也推荐使用同一份全模型 target（`format: table`，与其他共享 measurement 的 panel 使用完全一致的 URL + body），再接三段 transform。

### transform 链：`filterByValue → organize → reduce`

```json
"targets": [{
  "format": "table",
  "columns": [
    {"selector": "_time", "text": "Time", "type": "timestamp"},
    {"selector": "_value", "text": "Value", "type": "number"},
    {"selector": "prop", "text": "Prop", "type": "string"}
  ],
  "url": "/api/v1/query/<fullModelLongstmtUri>",
  "url_options": {"data": "<identical body, no prop filter>"}
}],
"transformations": [
  {"id": "filterByValue", "options": {
    "filters": [{"fieldName": "Prop", "config": {"id": "regex", "options": {"value": "^VOL$"}}}],
    "type": "include", "match": "any"
  }},
  {"id": "organize", "options": {
    "excludeByName": {"Time": true, "Prop": true},
    "indexByName": {},
    "renameByName": {}
  }},
  {"id": "reduce", "options": {"reducers": ["lastNotNull"]}}
]
```

为什么 `organize` 必须存在：
- `filterByValue` 之后，frame 里仍然有 `Time`、`Value`、`Prop` 三列
- `reduce` 需要只面对一个数值列
- `organize` 通过 `excludeByName` 把非数值列排除掉，才能让 `reduce` 只作用在 `Value` 上

**常见失败**：
- 省略 `organize` 时，`reduce` 会因为看到多个 field 而输出 `No data`
- `filterByValue` 的 `equal` 模式在当前 Infinity 版本里会静默失败；必须改用 regex 精确匹配，例如 `^VOL$`

## 多面板共享查询模式

当一个 dashboard 的多个 panel 来自同一 measurement，但展示不同 prop 子集时：

1. **所有 panel 的 target 必须完全一致**：同一 `url`、同一 `url_options.data`、同一 `columns`。这样 TSS 才能缓存并复用一次整模型响应。
2. **每个 panel 只改 transform 链**：
   - 多序列面板：`filterByValue → partitionByValues → prepareTimeSeries`
   - 单值面板：`filterByValue → organize → reduce`
3. **写完 JSON 后应验证字节级一致性**：确保所有 target 的 `url` 和 `url_options.data` 真正完全相同。

例子：一个 8 面板 dashboard，包含 CUR 折线、TEMP 折线、以及 VOL / SOC / SOH / TEMP_FAN_SET / TEMP_MAX_HIS / CHARGE_TIMES15 等 stat 卡片——都可以共享一次 API 查询。

## 明确不可行的做法

详见：
- `references/infinity-multi-series-ruled-out.md`：多序列失败样式
- `references/infinity-single-value-ruled-out.md`：单值 stat 失败样式

以下方式都不要采用：
1. **`format: timeseries` + 字符串列**：只会生成一条序列，字符串列不会参与分流。
2. **`format: timeseries` + 每 target 一个 `filters` 数组**：Infinity 过滤器容易崩溃（`(e.value || []).map is not a function`）或直接 `No data`。
3. **`filterByName` / `filterFieldsByName` transform**：Infinity 返回 field 名称与预期不一致，筛选经常失效。
4. **`format: series`**：行为与 timeseries 类似，仍不会按字符串列自动拆分。
5. **`filterByValue` 的 `equal` 模式**：当前版本会静默失败，应统一使用 regex `^PROP$`。
6. **`filterByValue → reduce` 且没有 `organize`**：stat 面板会 `No data`，因为 reduce 不知道该压缩哪个字段。

## 面板类型映射

- trend：Time series
- ranking：Bar chart 或 Table
- status：Stat、Gauge 或 Table
- anomaly：Table
- comparison：Time series 或 Bar chart
- benchmark：Bar chart、Table 或 Time series

## Infinity + TSS 规则

1. 按 SOP 中约定的 Grafana folder / datasource 规范落板。
2. 只要可能，就优先使用 TSS longstmt + Infinity，而不是直接把 InfluxDB token 暴露给 Grafana 面板。
3. Infinity target JSON 中统一使用：`type: json`、`parser: backend`、`root_selector: $.data.rows`。
4. 通过 datasource base URL 时，优先写相对路径 `/api/v1/query/{uri_segment}`。
5. 默认优先消费“全模型 longstmt + transforms”；只有 transforms 明确异常或用户要求按单 prop 拆查询时，才退回 `args.prop` 多 target 方案。
6. 当 Grafana 跑在 Docker 中时，它访问宿主机 TSS 应使用 Docker bridge gateway，而不是容器自己的 `localhost`。

### Infinity POST body 必须包含 args 包装层

TSS longstmt 的 HTTP API 期望请求体格式为 `{"args": {"1": "<start>", "2": "<stop>"}}`。Infinity `url_options.data` 字段是**原始 POST body 字符串**，因此必须包含 `args` 包装：

- 正确：`"data": "{\"args\": {\"1\": \"${__from:date:iso}\", \"2\": \"${__to:date:iso}\"}}"`
- 错误：`"data": "{\"1\": \"${__from:date:iso}\", \"2\": \"${__to:date:iso}\"}"` （缺少 args 包装，TSS 返回 500 Internal Server Error）

**诊断方法**：如果 Grafana ds/query API 返回 `error: "unsuccessful HTTP response code status code: 500 Internal Server Error"`，而直接 curl TSS 返回 200，检查 `url_options.data` 是否包含 `args` 包装层。

### TDengine longstmt 设计：prop 集合参数化查询

TDengine 共享超表的 COUNT(*) 返回原始行数（数十万至数亿），远超 TSS 的 1000 上限。解决方案是 **prop 集合参数化 longstmt**：将 prop 集合作为 `?` 占位符传入查询，每个 Grafana 面板传入自己需要的 prop 集合，count_stmt 与 stmt 的 WHERE 条件完全一致。

```sql
-- stmt：按 prop 集合查询，PARTITION BY + INTERVAL 降采样
SELECT LAST(val), LAST(ts) FROM `dedge_DOUBLE` WHERE ts > ? AND ts < ? AND tm_code = '<tm_code>' AND prop IN (?) PARTITION BY prop INTERVAL(10s)

-- count_stmt：投影字段改为 COUNT(*) + 子查询包裹，其余 WHERE/PARTITION BY/INTERVAL 与 stmt 完全一致
SELECT COUNT(*) FROM (SELECT COUNT(*) FROM `dedge_DOUBLE` WHERE ts > ? AND ts < ? AND tm_code = '<tm_code>' AND prop IN (?) PARTITION BY prop INTERVAL(10s))
```

Grafana 面板的 `url_options.data` 传入三个参数：
```json
{"args": {"1": "${__from:date:iso}", "2": "${__to:date:iso}", "3": "CUR1,CUR2,CUR3"}}
```

每个面板通过 `args.3` 指定 prop 集合（逗号分隔），TSS 只返回指定 prop 集合的数据。单 prop 5 分钟 INTERVAL(10s) 聚合后约 30 行，远低于 1000 限制。

**count_stmt 规则（强制）**：
- **子查询包裹**：当 stmt 含 `INTERVAL` 聚合时，count_stmt 必须用 `SELECT COUNT(*) FROM (<原 count_stmt>)` 子查询包裹。其中 `<原 count_stmt>` 是指将 stmt 的投影字段改为 `COUNT(*)` 后得到的查询（其余 WHERE、PARTITION BY、INTERVAL 等与 stmt 完全一致），再在外层用 `SELECT COUNT(*) FROM (...)` 包裹以统计聚合后的行数。不能直接写 `SELECT COUNT(*) FROM <表> WHERE ...` 省略 `PARTITION BY` 和 `INTERVAL`，否则 count 结果与 stmt 实际处理的数据量不一致。
- **一致性**：count_stmt 与 stmt 不允许有任何差异，除已描述的差异（投影字段改为 `COUNT(*)` + 子查询包裹）外，其余一切（WHERE、PARTITION BY、INTERVAL 等）必须完全一致。禁止通过额外过滤条件（如 `AND prop = 'xxx'`）人为压低 count 值来绕过 1000 限制。count_stmt 的职责是如实反映 stmt 将处理的数据量。
- **参数共享**：count_stmt 和 stmt 共享同一份 `args`，始终接收相同的时间范围和 prop 集合。

**Grafana 面板设计**：每个面板一个 target，通过 `args.3` 指定 prop 集合（逗号分隔）。不再需要 filterByValue transformation 做数据过滤（但仍可使用 partitionByValues + prepareTimeSeries 将返回数据格式化为时序）。

## 必要写回动作

每次创建或更新看板/面板后，必须执行：
1. 通过 Grafana MCP / API 获取该 dashboard 的公开分享信息。
2. 更新 `dedge-datacenter/catalog/dashboard-catalog.json`，至少写入：
   - `dashboardUrl`
   - `dashboardShareUrl`（尽量保留 `orgId`、`from`、`to`、`timezone`、`shareView=public_dashboard`）
   - `iframeUrl`：公开看板地址 `{agentmemory.grafana.publicDashboardBaseUrl}/<accessToken>`
   - `publicDashboardUid` / `publicDashboardAccessToken`
   - 面板类型、查询摘要、模型上下文、TSS 上下文、tags、修改历史
3. 用该公开 `iframeUrl` 更新 `currentView`；如果 backend 运行中，优先走 `POST /api/current-view`。
4. 调用 `POST {agentmemory.backend.notifyFrontendRefreshUrl}`，并带上 `targetClientId`，只让目标前端 WS 会话重新通过 axios 拉取。

## 运维排障

### 看板全空白：先查数据源认证

**症状**：所有看板（包括曾经正常的）面板区域全空白，浏览器 console 出现 `[FilterByValue] Could not find index for field name: Prop`。

**根因**：TSS 数据源密码过期/不匹配。Infinity 插件通过 Grafana proxy 请求 TSS 时带 basic auth，密码过期则 TSS 返回 401，Infinity 得到空响应，transforms 找不到列名。

**诊断步骤**：
```bash
# 1. 确认 TSS 本身可用（CLI 用自己的认证，不受 Grafana 密码影响）
dedge tss tsdb connect-ping --tds_code influxdb-v2-impl --json

# 2. 从 Docker 内测试 TSS endpoint（模拟 Grafana proxy 视角）
cat .dedge/tss/login                           # 拿到 TSS 密码
docker exec grafana curl -s -w "\nHTTP:%{http_code}" \
  -X POST "{agentmemory.tss.dockerReachableUrl}/api/v1/query/<uri>" \
  -u "admin:<tss_password>" \
  -H "Content-Type: application/json" \
  -d '{"args":{...}}'
# 如果返回 401 → 密码错误
# 如果返回 200 + 数据 → 密码正确，问题在 Grafana 侧
```

**修复**：
```bash
# 用 TSS 实际密码更新 Grafana datasource
curl -s -X PUT {agentmemory.grafana.url}/api/datasources/uid/<datasource_uid> \
  -H "Authorization: Bearer $(grep GRAFANA_SERVICE_ACCOUNT_TOKEN .hermes/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"name":"DEDGE-TSS-LongQuery","type":"yesoreyeram-infinity-datasource",
       "url":"{agentmemory.tss.dockerReachableUrl}","access":"proxy","basicAuth":true,
       "basicAuthUser":"admin","secureJsonData":{"basicAuthPassword":"<tss_password>"},
       "jsonData":{"auth_method":"basicAuth"}}'

# 验证修复
curl {agentmemory.grafana.url}/api/datasources/uid/<datasource_uid>/health
# 应返回 {"message":"Health check successful","status":"OK"}
```

### `update_dashboard` overwrite 可能创建新看板

使用 `update_dashboard(uid=X, overwrite=true, dashboard={...})` 时，如果 Grafana 无法匹配内部 `id`，它不会覆盖原看板而是**创建一个新的 UID**。**始终检查返回的 `uid`，不要假设与原 UID 相同。** 如发现 UID 变化，删除旧看板，更新 catalog 和 public dashboard。

### 公共看板 timeSelectionEnabled 必须为 true

创建 public dashboard 时务必传 `"timeSelectionEnabled": true`，否则用户无法切换时间范围。初始创建 API：
```json
POST /api/dashboards/uid/<uid>/public-dashboards
{"isEnabled":true,"timeSelectionEnabled":true,"share":"public"}
```
如果创建时忘了，用 `PATCH` 同一 endpoint 补上。

### 大时间范围导致数据溢出

50ms 采样 × 63 props → 5 分钟约 375K 行（在 500K limit 内）。24 小时约 108M 行，远超 TSS longstmt 的 `limit(n: 500000)`。创建看板时的时间范围选择：
- 默认推荐 `now-5m`，与现有看板保持一致
- 若用户要求更长范围，优先同步增大 SQL/TSS 侧平均窗口，先把总点数压到约 30，再决定是否扩展到 `15m`、`1h`
- 只有用户明确要求原始点明细时，才允许取消平均；此时要主动评估 limit 与渲染成本
- `6h+` 且仍需较高分辨率时，需改用按 prop 过滤的 longstmt，或缩短时间窗口

### 浏览器截图验证：必须等待数据加载

Grafana 面板数据加载需要时间（特别是全模型长查询），浏览器截图太早会捕获空白页面。

**强制规则**：
1. 打开看板后，**必须等待至少 5 秒**再截图或取快照。
2. 如果 5 秒后仍无数据（快照中面板无 Canvas 或无 legend），再等 5 秒后重试。
3. 优先使用 `browser_snapshot(full=true)` 做文本级验证——能直接看到 legend 中的测点名称和数值（如 `TEMP_AVG: 42.8 °C`、`CUR1: 47.1 A`），比截图更可靠。
4. 截图仅作为辅助手段，以文本快照确认为准。

**常见误判**：面板标题已出现（region 可见），但截图空白 → 不是配置问题，是渲染未完成。

### verify 验证数据优先用 API，不依赖浏览器截图

浏览器自动化工具渲染 Grafana 经常出现空白（`Cancel` 按钮持续显示），不代表数据不通。首选 API 验证：
```bash
# 直接通过 Grafana ds/query API 确认数据返回
curl -s -X POST {agentmemory.grafana.url}/api/ds/query \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"queries":[{...}],"from":"...","to":"..."}'
```
确认 `frames[0].schema.fields` 包含 `Prop`、`Time`、`Value` 且 `data.values` 非空即可认定数据通路正常。

## 权威来源

1. Grafana 的实时行为，以及当前 backend/catalog 集成的真实行为。
2. `dedge-datacenter/.hermes/` 下本技能及同级 bundled skills。
3. `dedge-datacenter/` 内项目资产文件。
4. 仅当当前环境确实存在时，才把 harness 根目录 docs 作为补充参考。
