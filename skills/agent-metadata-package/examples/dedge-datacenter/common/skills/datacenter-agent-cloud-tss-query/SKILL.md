---
name: datacenter-agent-cloud-tss-query
description: 勘探 dedge Cloud 物模型，并规划/执行 TSS 查询，覆盖 longstmt 成功样本流程、TypeFrame 校验与当前数据源记忆假设。
---

# dedge Cloud + TSS 查询

当任务涉及“把用户指标映射到物模型属性”或“执行/规划 TSS 查询”时，使用本技能。

## 数据源记忆规则

开始做 TSS 工作前，先读取项目外接记忆文件：

`dedge-datacenter/runtime/agent-memory/tsdb-memory.json`

当前 MVP 假设：
- 数据源事实存放在该项目文件中，而不是 Hermes 私有 memory
- 当前默认只有一个主时间序列数据源上下文
- 该数据源被视为覆盖全部当前物模型

下一版本提醒：
- 后续 agent 需要学会区分“哪个数据源服务哪个物模型”，而不是继续假设一个数据源覆盖全部模型

## Cloud 勘探

1. 如果当前并不知道目标模型，先从大范围开始：`dedge cloud tm tree --json`。
2. 在决定属性前，先导出或列出候选物模型的属性。
3. 把用户指标映射到 `tm_code`、`prop`、`td_data_type`，必要时补充 `tl_code`。
4. 如果存在多个合理映射，必须澄清。

## TSS 规划

1. 查询前先从项目外接记忆或环境中解析当前 `tds_code`。
2. 正式查询前，先用 `dedge tss tsdb connect-ping --tds_code <tds_code> --json` 检查数据源可用性。
3. 简单单点查询优先使用 tmagg query。
4. 面向 Grafana 的参数化查询优先使用 stmt-query / longstmt。
5. 每次都必须检查 TypeFrame 的 `code`、`data.columns`、`data.rows`、`data.meta`。

## longstmt 规则

不要直接创建 longstmt。验证过的正确顺序是：

1. 先用同一份参数化模板和一组样例参数执行一次 `stmt-query`，让 TSS 记录 `stmt_success` 样本。
2. 再用同一份模板与合法 `schema_json` 执行 `longstmt up`。
3. 最后通过 `POST /api/v1/query/{uri_segment}` 或 `dedge tss longstmt exec` 执行。

### stmt-query body 格式

stmt-query 的 body 使用 `args`（不是 `params`）传模板替换值：

```json
{
  "count_stmt": "from(bucket: params.bucket) |> range(start: time(v: params.start), stop: time(v: params.stop)) |> filter(fn: (r) => r[\"_measurement\"] == params.measurement) |> filter(fn: (r) => r[\"tl_code\"] == params.tl_code) |> filter(fn: (r) => r[\"_field\"] == \"val\") |> filter(fn: (r) => contains(value: r.prop, set: params.props)) |> count()",
  "stmt": "from(bucket: params.bucket) |> range(start: time(v: params.start), stop: time(v: params.stop)) |> filter(fn: (r) => r[\"_measurement\"] == params.measurement) |> filter(fn: (r) => r[\"tl_code\"] == params.tl_code) |> filter(fn: (r) => r[\"_field\"] == \"val\") |> filter(fn: (r) => contains(value: r.prop, set: params.props)) |> sort(columns: [\"_time\"]) |> limit(n: 500000)",
  "args": {
    "bucket": "dedge",
    "start": "2026-07-10T02:24:00Z",
    "stop": "2026-07-10T02:27:00Z",
    "measurement": "dadevice-coll-1_double_4e7cde5f",
    "tl_code": "deploy-tl-main",
    "props": ["VOL", "CUR1", "TEMP_AVG"]
  }
}
```

关键点：模板里依然写 `params.xxx`，但真正传入的替换值放在 `args` 下。

注意: `count_stmt` 在 CLI schema 中是 required 字段，不是可选建议。上述 Flux 示例仅展示 `stmt` 和 `args`，实际请求还需包含 `count_stmt` 字段（一个 COUNT 型先验查询，返回值需足够小才放行 `stmt`）。缺失 `count_stmt` 会被 schema 校验直接拒绝，命令不会执行。

### count_stmt 规则（Flux 版，强制）

**子查询包裹（Flux 等价）**：当 stmt 含 `aggregateWindow` 聚合时，count_stmt 不能只做简单 `|> count()`，必须与 stmt 共享完全相同的管道（range、filter、aggregateWindow 等），仅将末尾的 `|> sort() |> limit()` 替换为 `|> count()`。这等价于 SQL 的 `SELECT COUNT(*) FROM (<原 stmt>)` 子查询包裹。

stmt 模板（含 aggregateWindow）：
```flux
from(bucket: params.bucket)
  |> range(start: time(v: params.start), stop: time(v: params.stop))
  |> filter(fn: (r) => r["_measurement"] == params.measurement)
  |> filter(fn: (r) => r["tl_code"] == params.tl_code)
  |> filter(fn: (r) => r["_field"] == "val")
  |> filter(fn: (r) => contains(value: r.prop, set: params.props))
  |> aggregateWindow(every: duration(v: params.interval), fn: mean, createEmpty: false)
  |> sort(columns: ["_time"])
  |> limit(n: 500000)
```

对应 count_stmt 模板（共享同一管道，末尾改为 count）：
```flux
from(bucket: params.bucket)
  |> range(start: time(v: params.start), stop: time(v: params.stop))
  |> filter(fn: (r) => r["_measurement"] == params.measurement)
  |> filter(fn: (r) => r["tl_code"] == params.tl_code)
  |> filter(fn: (r) => r["_field"] == "val")
  |> filter(fn: (r) => contains(value: r.prop, set: params.props))
  |> aggregateWindow(every: duration(v: params.interval), fn: mean, createEmpty: false)
  |> count()
```

**一致性**：count_stmt 与 stmt 不允许有任何差异，除已描述的差异（末尾投影改为 `count()` 替代 `sort + limit`）外，其余一切（range、filter、aggregateWindow 等）必须完全一致。禁止通过额外过滤条件或省略聚合步骤来人为压低 count 值绕过 1000 限制。count_stmt 的职责是如实反映 stmt 将处理的数据量。

**参数共享**：count_stmt 和 stmt 共享同一份 `args`，始终接收相同的时间范围和 prop 集合。

### longstmt `schema_json` 格式

`longstmt up` body 中的 `schema_json` 必须是 JSON **对象**，不能是“JSON 字符串”：

```json
{
  "schema_json": {
    "type": "object",
    "properties": {"bucket": {"type": "string"}, ...},
    "required": ["bucket", ...]
  }
}
```

如果写成 `"schema_json": "{\"type\":\"object\",...}"` 这种双重编码字符串，会报：`schema_json parse failed: invalid argument`。

### stmt_hash 一致性

TSS 会按“完整模板字符串”的 hash 匹配 stmt-query 与 longstmt up。两边模板必须 **逐字节完全一致**，包括 `limit(n: N)`。如果 stmt-query 用 `limit(n: 100)`，而 longstmt up 用 `limit(n: 500000)`，hash 就不同，最终会因为找不到成功样本而失败，报 `stmt success sample not found`。

## longstmt 访问策略

TSS 具备短时查询缓存。面向 Grafana 创建 longstmt 时，**默认优先创建"prop 集合参数化 longstmt"**：

1. 通过 `params.props`（数组）传入 prop 集合，一次返回指定 prop 的数据。
2. `schema_json.required` 默认包含：`bucket`、`start`、`stop`、`measurement`、`tl_code`、`props`。
3. Grafana 多 panel 并发访问同一 URL + body 时，优先依赖 TSS 缓存命中。
4. 只有在 transforms 明确不可用或用户要求不带 prop 过滤返回全量 prop 时，才退回不带 `props` 参数的 longstmt。

### prop 集合参数化模板示例

stmt 模板（含 prop 集合过滤）：
```
from(bucket: params.bucket)
  |> range(start: time(v: params.start), stop: time(v: params.stop))
  |> filter(fn: (r) => r["_measurement"] == params.measurement)
  |> filter(fn: (r) => r["tl_code"] == params.tl_code)
  |> filter(fn: (r) => r["_field"] == "val")
  |> filter(fn: (r) => contains(value: r.prop, set: params.props))
  |> sort(columns: ["_time"])
  |> limit(n: 500000)
```

对应 count_stmt 模板（共享同一管道，末尾改为 count）：
```
from(bucket: params.bucket)
  |> range(start: time(v: params.start), stop: time(v: params.stop))
  |> filter(fn: (r) => r["_measurement"] == params.measurement)
  |> filter(fn: (r) => r["tl_code"] == params.tl_code)
  |> filter(fn: (r) => r["_field"] == "val")
  |> filter(fn: (r) => contains(value: r.prop, set: params.props))
  |> count()
```

对应 schema 包含：`bucket`、`start`、`stop`、`measurement`、`tl_code`、`props`（数组类型）。

### 推荐 CLI 流程

1. 用包含 prop 集合过滤的模板先跑一次 `stmt-query`。
2. 用完全同一份模板执行 `longstmt up`。
3. 用 `longstmt exec` 或 HTTP `POST /api/v1/query/{uri_segment}` 验证返回 TypeFrame。

示意命令：

```bash
cat <<'EOF' >/tmp/prop-set-stmt.json
{
  "count_stmt": "from(bucket: params.bucket) |> range(start: time(v: params.start), stop: time(v: params.stop)) |> filter(fn: (r) => r[\"_measurement\"] == params.measurement) |> filter(fn: (r) => r[\"tl_code\"] == params.tl_code) |> filter(fn: (r) => r[\"_field\"] == \"val\") |> filter(fn: (r) => contains(value: r.prop, set: params.props)) |> count()",
  "stmt": "from(bucket: params.bucket) |> range(start: time(v: params.start), stop: time(v: params.stop)) |> filter(fn: (r) => r[\"_measurement\"] == params.measurement) |> filter(fn: (r) => r[\"tl_code\"] == params.tl_code) |> filter(fn: (r) => r[\"_field\"] == \"val\") |> filter(fn: (r) => contains(value: r.prop, set: params.props)) |> sort(columns: [\"_time\"]) |> limit(n: 500000)",
  "args": {
    "bucket": "dedge",
    "start": "2026-07-10T02:24:00Z",
    "stop": "2026-07-10T02:29:00Z",
    "measurement": "dadevice-coll-1_double_4e7cde5f",
    "tl_code": "deploy-tl-main",
    "props": ["VOL", "CUR1", "CUR2", "TEMP_AVG"]
  }
}
EOF

dedge tss tsdb stmt-query --tds_code <tds_code> --file /tmp/prop-set-stmt.json
```

`--tds_code` 是必填参数，值为数据源编码。tds_code 可从 agent-memory 文件 (runtime/agent-memory/tsdb-memory.json) 中获取，或通过 Cloud 拓扑查询获取。

```bash
cat <<'EOF' >/tmp/prop-set-longstmt.json
{
  "tds_code": "<tds_code>",
  "stmt": "from(bucket: params.bucket) |> range(start: time(v: params.start), stop: time(v: params.stop)) |> filter(fn: (r) => r[\"_measurement\"] == params.measurement) |> filter(fn: (r) => r[\"tl_code\"] == params.tl_code) |> filter(fn: (r) => r[\"_field\"] == \"val\") |> filter(fn: (r) => contains(value: r.prop, set: params.props)) |> sort(columns: [\"_time\"]) |> limit(n: 500000)",
  "count_stmt": "from(bucket: params.bucket) |> range(start: time(v: params.start), stop: time(v: params.stop)) |> filter(fn: (r) => r[\"_measurement\"] == params.measurement) |> filter(fn: (r) => r[\"tl_code\"] == params.tl_code) |> filter(fn: (r) => r[\"_field\"] == \"val\") |> filter(fn: (r) => contains(value: r.prop, set: params.props)) |> count()",
  "schema_json": {
    "type": "object",
    "required": ["bucket", "start", "stop", "measurement", "tl_code", "props"],
    "properties": {
      "bucket": {"type": "string"},
      "start": {"type": "string"},
      "stop": {"type": "string"},
      "measurement": {"type": "string"},
      "tl_code": {"type": "string"},
      "props": {"type": "array", "items": {"type": "string"}}
    }
  },
  "enabled": true
}
EOF

dedge tss longstmt up --file /tmp/prop-set-longstmt.json
```

### 输入/输出结构速记

- `stmt-query` 输入：`{"count_stmt":"...params.xxx...|> count()","stmt":"...params.xxx...","args":{"bucket":"...","start":"...","stop":"...","measurement":"...","tl_code":"...","props":[...]}}`
- `stmt-query` 输出：TypeFrame，重点检查 `code`、`data.columns`、`data.rows`
- `longstmt up` 输入：`{"tds_code":"...","stmt":"...","count_stmt":"...","schema_json":{"required":["bucket","start","stop","measurement","tl_code","props"],...},"enabled":true}`
- `longstmt up` 输出：长查询条目，重点记录 `uri_segment`
- `longstmt exec` 输入：`{"args":{"bucket":"...","start":"...","stop":"...","measurement":"...","tl_code":"...","props":[...]}}`
- `longstmt exec` 输出：TypeFrame；prop 集合参数化模式下 `rows[*]` 通常至少包含 `_time`、`_value`、`prop`

### 访问技巧

1. **默认传入 prop 集合**：通过 `params.props` 数组传入所需 prop 列表，TSS 只返回指定 prop 的数据，减少返回量和缓存压力。
2. **样例时间窗先用 5 分钟**：便于验证返回量与 Grafana 默认时间窗一致。
3. **确认 body 一致性**：想吃到缓存，Grafana 各 panel 的 `url_options.data` 必须字节级一致（包括 `props` 数组）。
4. **不带 prop 过滤兜底仍然有效**：若需要全量 prop 且 transforms 可处理，可不传 `props` 参数返回全量数据。

## TSS 查询安全规则（必须遵守）

以下规则无例外地必须遵守。违反任何一条都可能导致系统宕机。无论查询目的如何、无论 COUNT 结果如何、无论排查还是业务查询，都不允许跳过这些规则。

**绝对禁令：禁止不携带时间范围、INTERVAL 降采样、tm_code/filters 等限制条件就进行全表扫描。** 无论是 COUNT、SELECT、还是验证性查询，都必须携带时间范围和过滤条件。无时间范围的全表扫描可能导致 TDengine 扫描数亿行数据，造成系统资源耗尽。唯一的例外是 SHOW STABLES、DESCRIBE、SHOW TABLES 等纯元数据命令。

### 规则一：TSS 查询必须携带时间范围，必须先 COUNT

向 TSS 发起任何数据查询时：

1. 必须携带时间范围（`ts > ? AND ts < ?`），禁止以任何理由省略。
2. 必须先用 COUNT 查询数据规模，禁止以任何理由跳过。
3. COUNT 也必须携带时间范围和 tm_code 过滤，从窄窗（5分钟）开始逐步扩大。
4. 即便目的是"确认数据是否存在"或"查看最新一条"，也必须遵守上述规则——不存在"只看一条所以不需要时间范围"的例外。
5. COUNT 返回 0 是查询正常完成、结果值为 0 的正常结果，不是异常。此时应逐步扩大时间范围继续排查（如 5 分钟 → 1 小时 → 24 小时 → 7 天），扩大时仍须携带时间范围和 tm_code 过滤，并遵循其他规则。只有查询报错或超时未返回时才是异常行为，需要上报用户。经过合理范围逐步扩大后仍无数据，可结合元数据命令排查并向用户报告结论。禁止以"COUNT 返回 0 所以换其他方式"为由转向无时间范围或无 tm_code 的全扫描查询。

### 规则二：通用数据安全意识（适用于所有搜索，不限于 TSS）

在 TSS 之外的任何搜索过程中（包括但不限于 Cloud API 查询、数据库元数据扫描、文件搜索、HTTP 接口调用），也必须遵循数据量控制原则：

1. 搜索前先评估：当前搜索方式可能导致处理的数据量有多大？是否有可能导致系统资源耗尽？
2. 寻找能够预估数据量的方法（如元数据命令、LIMIT 1 试探、分页计数等），根据预估数据量采取不同搜索策略。
3. 任何搜索查询都必须携带过滤条件，控制返回数据量。禁止无条件全量搜索。
4. 如果按照上述策略仍然无法搜索到结果，向用户报告搜索过程和结论，等待用户反馈。禁止无脑扩大搜索范围或切换到全量扫描。

以下为具体策略细则，是上述两条规则的实施规范。

### 背景：数据库规模假设

当前查询的对象可能是数据量极大的数据库。每个 prop 每 10ms 就会写入一条记录，数百个 prop 共享同一张超表时，1 分钟即可产生数百万行。所有策略都基于这一前提设计——任何没有时间范围或时间范围过大的查询都可能导致系统资源耗尽。

### 补充规则：COUNT 查询本身也可能超时

当数据量庞大时，即使 COUNT 查询带了时间范围和 tm_code 过滤，也可能无法在 5 秒内返回。此时不能认为 COUNT 是"轻量"的，需要进一步缩减查询规模：
- 5 分钟 COUNT 超时 → 收窄到 1 分钟
- 1 分钟 COUNT 超时 → 收窄到 10 秒
- 10 秒 COUNT 仍超时 → 按策略四第二级处理，停止查询并反馈用户

### 补充规则：检测表或数据是否存在时从小范围开始

如果查询目的仅为检测表或表中数据是否存在（而非获取业务数据），应从最小范围开始查询：
1. 先查最近 1 分钟范围（带 tm_code 过滤，LIMIT 1）
2. 如果有数据返回，说明表存在且有数据，无需扩大
3. 如果没有数据，逐步扩大范围（1 分钟 → 5 分钟 → 1 小时 → …），每步扩大前先用 COUNT 评估该范围的规模
4. 如果扩大到 1 小时仍无数据，说明该表可能确实没有近期数据，反馈用户而非继续扩大

禁止为了"确认数据是否存在"而直接查询大时间范围。

### 教训：优先元数据命令，禁止用数据扫描代替元数据查询

查询前必须明确目的，优先使用 TSS/Cloud 提供的元数据命令（`gen-table-name`、`SHOW STABLES`、`DESCRIBE`、`SHOW TABLES`）获取信息。当元数据命令无法搜索到所需信息时，必须询问用户如何进一步处理——告知用户可以采用数据扫描方式排查，但需说明大量数据查询可能导致资源耗尽的风险，由用户确认后才执行。禁止边查边想、逐表试探式扫描。

### 策略一：验证性查询用最小代价模式

验证表是否存在、列结构是否正确、longstmt 是否可用——这类查询不需要大量数据。

- 验证表存在：`SHOW TABLES` / `SHOW STABLES` + 内存中过滤表名，不直接 `SELECT COUNT(*) FROM 超表`
- 验证表结构：`DESCRIBE 表名`（元数据操作，不扫数据）
- 验证 longstmt 可用性：查询最近 5 分钟范围（`WHERE ts > ? AND ts < ?` 带显式窄时间窗），而非全表或大范围
- 验证列名：`SELECT * FROM 表名 WHERE ts > now-5m LIMIT 1`（窄窗 + LIMIT 1），而非无时间范围 LIMIT 5

### 策略二：数据查询前先 COUNT 评估规模

对任何超表/大表执行业务查询前，必须先执行一次轻量 COUNT 评估数据规模：

```sql
SELECT COUNT(*) FROM `表名` WHERE ts > '开始时间' AND ts < '结束时间' AND tm_code = '...'
```

关键约束：
- COUNT 必须带时间范围，禁止全表 COUNT
- 时间范围从窄到宽递进：先查 5 分钟，再逐步扩大
- 如果 5 分钟内 COUNT 就超时，说明写入速率极高，必须进一步收窄到 1 分钟甚至更小

### 策略三：根据规模选择降采样 INTERVAL

COUNT 结果出来后，按以下阈值选择策略：

| 预估行数 | 策略 |
|---|---|
| < 1万 | 直接查询，无需降采样 |
| 1万 ~ 10万 | INTERVAL(10s) 降采样 |
| 10万 ~ 100万 | INTERVAL(1m) 降采样 |
| > 100万 | INTERVAL(10m) 或更大，且必须加 LIMIT |
| 5秒内未返回 | 放弃当前查询，进一步缩小时间范围或加大 INTERVAL |

### 策略四：超时分两级处理

- **第一级**：原查询超时 → 禁止重试相同或更大范围的查询，必须将时间范围缩小到 5 分钟窄窗重新查询
- **第二级**：5 分钟窄窗也超时 → 停止查询，将异常反馈给用户，报告内容包含：查询的表名、SQL 语句、时间范围、超时现象，由用户决定下一步

禁止超时后直接发起另一个大查询导致多个查询叠加。无法精准 KILL 自己发起的查询（TSS 连接池对 agent 不可见，connection_id 无法定位），因此只能靠预防。

### 策略五：INTERVAL 与时间范围联动

- INTERVAL(10s) 仅适用于 1 小时以内的范围（1h × 62prop × 10s ≈ 22320 行，可接受）
- 范围 > 1 小时，INTERVAL 自动升级：1h-24h 用 INTERVAL(1m)，1d-7d 用 INTERVAL(10m)，> 7d 用 INTERVAL(1h)
- 结果集预估公式：`时间范围秒数 / INTERVAL秒数 × prop数量`，超过 10 万行必须加 LIMIT 或加大 INTERVAL

### 策略六：超表查询必须带 tm_code + 时间范围

- 禁止对 `dedge_DOUBLE` / `dedge_INT` / `dedge_BOOL` 等共享超表执行无 `tm_code` 过滤的查询
- 禁止无时间范围查询（即使带 LIMIT，TDengine 也可能全表扫描）
- 唯一例外：`SHOW STABLES`、`DESCRIBE`、`SHOW TABLES` 等元数据操作

## SOP 易错点

- Grafana 里的 Flux 时间变量必须是 ISO：`${__from:date:iso}` / `${__to:date:iso}`。
- 对 50ms 采样数据，`limit(n: 500)` 明显过小；覆盖 Grafana 时间窗时至少使用 50000 以上。
- 没有真实查询输出时，不要宣称成功。

## 权威来源

1. 当前部署项目中的实时 Cloud/TSS 命令输出与 HTTP 行为。
2. `dedge-datacenter/.hermes/` 下本技能及同级 bundled skills。
3. `dedge-datacenter/` 内项目资产文件，尤其是外接数据源记忆文件。
4. 仅当当前环境确实存在时，才把 harness 根目录 docs 作为补充参考。
