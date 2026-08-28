---
name: datacenter-agent-tdengine-longstmt
description: Use when TDengine data needs longstmt queries for Grafana.
---

# TDengine Longstmt for Grafana

When a dedge thing model's time-series data lives in TDengine (not InfluxDB), the Flux-based longstmt workflow in `datacenter-agent-cloud-tss-query` does not apply. TDengine uses SQL with `?` positional placeholders. Use this skill to create working longstmt entries that Grafana Infinity panels can consume.

## When to use this skill

- `dedge tss tsdb stmt-query` with Flux syntax returns `code: 4` on a data source.
- `dedge ts-singleserver tsdb connect-ping` succeeds for `TDengine_network_server` but InfluxDB returns 0 rows.
- You need to create longstmt entries for a tm_code that spans multiple td_data_type tables.

## CLI command prefix

The top-level dedge command has a `tss` subcommand (not `ts-singleserver`). All TSS CLI commands use `dedge tss` as the prefix:

```
dedge tss login <url> <user> <password>
dedge tss status --json
dedge tss tsdb connect-ping --tds_code <tds_code> --json
dedge tss tsdb gen-table-name --tds_code <tds_code> --file <json>
dedge tss tsdb query --tds_code <tds_code> --data '<json>'
dedge tss tsdb stmt-query --tds_code <tds_code> --file <json>
dedge tss longstmt ls --json
dedge tss longstmt get -id <id> --json
dedge tss longstmt up --file <json>
dedge tss longstmt exec --uri <uri_segment> --json
```

**Pitfall**: `dedge ts-singleserver` is NOT a valid command prefix — it returns the top-level dedge help text. Always use `dedge tss`. The `--json` flag is optional for most commands; `--tds_code` is always required for tsdb subcommands.

## Discovery: one tm_code to multiple tables

A single thing model (`tm_code`) splits into separate TDengine measurement tables by `td_data_type`. Before creating longstmts, discover all tables:

```json
{
  "tmagg": {
    "tm_code": "DADEVICE_COLL_1",
    "tl_code": "test0212",
    "data_type": "DOUBLE",
    "prop": "VOL"
  }
}
```

Pass this as the body to `gen-table-name`. The response gives `main_table` (the measurement name) and `sub_table`. Repeat for each `td_data_type`. Each main_table needs its own longstmt.

**Cloud td_data_type → gen-table-name data_type mapping**: `DOUBLE`→`DOUBLE`, `INT`→`INT`, `BOOL`→`BOOL`, `LONG`→`BIGINT`. The `LONG` type is the most common gotcha — Cloud calls it `LONG` but TDengine/gen-table-name requires `BIGINT`. Always check `SHOW STABLES` to confirm the resulting supertable (e.g. `dedge_BIGINT`) actually exists before creating longstmts.

**Field name is `data_type`, not `td_data_type`.** Using `td_data_type` returns: `tmagg.data_type is required: invalid argument`.

## TDengine SQL template format

TDengine longstmts use SQL with `?` positional placeholders, not Flux `params.xxx`:

```sql
SELECT prop, LAST(val), LAST(ts) FROM `<main_table>` WHERE ts > ? AND ts < ? PARTITION BY prop INTERVAL(10s)
```

The `schema_json` uses numeric string keys matching positional order:

```json
{
  "schema_json": {
    "type": "object",
    "properties": {
      "1": {"type": "string", "description": "start time ISO8601"},
      "2": {"type": "string", "description": "end time ISO8601"}
    },
    "required": ["1", "2"]
  }
}
```

Execution args use the same numeric keys:

```json
{"args": {"1": "2026-07-28T00:00:00Z", "2": "2026-07-28T00:05:00Z"}}
```

## Correct creation sequence

1. Run `stmt-query` with the SQL template and sample args to register a success sample.
2. Run `longstmt up` with the identical template + `count_stmt` + `schema_json`.
3. Verify via HTTP: `POST /api/v1/query/{uri_segment}` with `{"args": {"1": "...", "2": "..."}}`.

If you skip step 1, `longstmt up` fails with: `stmt success sample not found before put query-entry: invalid argument`.

### `longstmt up` requires `count_stmt` as a required field

The `longstmt up` body MUST include `count_stmt` alongside `stmt`, `schema_json`, `tds_code`, and `enabled`. Omitting it returns `code: 3, msg: "invalid argument"` with no further explanation.

Correct `longstmt up` body (all required fields):

```json
{
  "tds_code": "TDengine_network_server",
  "stmt": "SELECT prop, LAST(val), LAST(ts) FROM `dedge_DOUBLE` WHERE ts > ? AND ts < ? AND tm_code = '<tm_code>' AND prop IN (?) PARTITION BY prop INTERVAL(10s)",
  "count_stmt": "SELECT COUNT(*) FROM (SELECT COUNT(*) FROM `dedge_DOUBLE` WHERE ts > ? AND ts < ? AND tm_code = '<tm_code>' AND prop IN (?) PARTITION BY prop INTERVAL(10s))",
  "schema_json": {
    "type": "object",
    "properties": {
      "1": {"type": "string", "description": "start time ISO8601"},
      "2": {"type": "string", "description": "end time ISO8601"},
      "3": {"type": "string", "description": "prop list, comma-separated (e.g. CUR1,CUR2,CUR3)"}
    },
    "required": ["1", "2", "3"]
  },
  "enabled": true
}
```

The `count_stmt` template uses the same `?` positional placeholders as `stmt`, with the same `args` mapping. At execution time, TSS runs `count_stmt` first; if the returned count exceeds the internal threshold (currently 1000), the `stmt` query is blocked with `code: 3, msg: "count_stmt result <N> exceeds max allowed 1000: invalid argument"`.

**count_stmt 规则（强制）**：
- **子查询包裹**：当 stmt 含 `INTERVAL` 聚合时，count_stmt 必须用 `SELECT COUNT(*) FROM (<原 count_stmt>)` 子查询包裹。其中 `<原 count_stmt>` 是指将 stmt 的投影字段改为 `COUNT(*)` 后得到的查询（其余 WHERE、PARTITION BY、INTERVAL 等与 stmt 完全一致），再在外层用 `SELECT COUNT(*) FROM (...)` 包裹以统计聚合后的行数。不能直接写 `SELECT COUNT(*) FROM <表> WHERE ...` 省略 `PARTITION BY` 和 `INTERVAL`，否则 count 结果与 stmt 实际处理的数据量不一致。
- **一致性**：count_stmt 与 stmt 不允许有任何差异，除已描述的差异（投影字段改为 `COUNT(*)` + 子查询包裹）外，其余一切（WHERE、PARTITION BY、INTERVAL 等）必须完全一致。禁止通过额外过滤条件或省略聚合子句来人为压低 count 值绕过 1000 限制。count_stmt 的职责是如实反映 stmt 将处理的数据量。
- **参数共享**：count_stmt 和 stmt 共享同一份 `args`，始终接收相同的时间范围和 prop 集合。不能为 count 使用更窄的时间窗或更小的 prop 集合。

### Existing longstmts with empty `count_stmt_template` must be re-created

Longstmt entries created in older TSS versions (or via APIs that didn't require `count_stmt`) may have an empty `count_stmt_template` field. When Grafana or HTTP queries hit such an entry, TSS returns:

```
code: 3, msg: "query-entry <uri_segment> has empty count_stmt_template; re-create it via PUT /query-entry with count_stmt: invalid argument"
```

**Fix**: re-run `longstmt up` with the same `stmt` template plus a `count_stmt` field. The URI segment stays the same (TSS matches by `stmt_hash`), so existing Grafana panels continue to work without URL changes. No need to delete the old entry first — `longstmt up` is an upsert.

### count_stmt 1000-row threshold and high-prop-count models

The TSS count_stmt threshold is 1000 rows. For models with hundreds of props at high sampling rates (e.g. 50ms), even a 1-minute window can exceed this limit:

| Prop count | Sampling | Rows/min | 1-min window | 10-sec window |
|---|---|---|---|---|
| 62 (DOUBLE) | 50ms | ~74,400 | Exceeds | ~1,240 (exceeds) |
| 452 (INT) | 50ms | ~542,400 | Exceeds (~6,800) | ~903 (under) |
| 51 (BOOL) | 50ms | ~61,200 | Exceeds (~1,020) | ~850 (under) |

When a longstmt query returns `count_stmt result <N> exceeds max allowed 1000`:
- **Do NOT widen the time range** — this makes the count worse.
- **Narrow the time range** to find a window where count < 1000. For 452 props at 50ms, a 10-second window yields ~903 rows (just under the limit).
- **Inform the user** that the dashboard's default time range (typically `now-5m`) may not work when data is actively flowing at high frequency. The user may need to select a shorter time range, or the INTERVAL should be increased (e.g. `INTERVAL(30s)` instead of `INTERVAL(10s)`) to reduce the row count per window.
- **When no data exists in the recent window**: count returns 0, which passes the threshold. The longstmt executes successfully but returns 0 rows. This is the expected behavior for models whose data pipeline has stopped — the dashboard shows "No data" until data resumes.

### Zero-data stmt-query still registers a valid success sample

A stmt-query that returns `code: 0` with `columns: []` and `rows: []` (completely empty TypeFrame — zero data in the time window) **still counts as a valid success sample**. `longstmt up` will succeed immediately after. This means you can pre-provision longstmts and Grafana dashboards for models that have no TDengine data yet (e.g. HSL device alive but MQTT uplink broken, or a newly commissioned model whose data pipeline hasn't started). Once data starts flowing into the supertable, the existing longstmt and dashboard panels will auto-populate without any further configuration changes.

The only requirement is that the stmt-query returns `code: 0` (success). A `code: 4` (Flux on TDengine) or connection error does NOT register a sample. If the supertable doesn't exist at all (e.g. `dedge_BIGINT` for a model with `td_data_type=LONG` but no data ever written), stmt-query returns `code: 4` with `[0x2603] Table does not exist` — this does NOT register a sample, and you should skip that data type entirely rather than retry.

## TypeFrame output structure

TDengine longstmt returns TypeFrame with columns:

- `timestamp` — interval bucket start (often `0001-01-01T00:00:00Z`, can be ignored)
- `last(ts)` — actual timestamp of the last data point in the interval (use as Grafana Time)
- `last(val)` — last value in the interval (use as Grafana Value)
- `prop` — property name (use as Grafana Prop for transform filtering)

## Infinity column mapping for TDengine

Unlike the Flux/InfluxDB longstmt which returns `_time`/`_value`/`prop`, TDengine returns `last(ts)`/`last(val)`/`prop`. Infinity columns must use these exact selectors:

```json
"columns": [
  {"selector": "last(ts)", "text": "Time", "type": "timestamp"},
  {"selector": "last(val)", "text": "Value", "type": "number"},
  {"selector": "prop", "text": "Prop", "type": "string"}
]
```

Additionally, the Infinity target must have `"source": "url"` at the **top level** of the target object (not just inside `url_options`), and `url_options` must include `"method": "POST"` plus all empty fields: `body_form:[]`, `params:[]`, `headers:[]`, `body_graphql_query:""`, `body_graphql_variables:""`, `global_query_id:""`.

### `url_options.method` must be explicitly set to `"POST"`

Infinity's `url_options` object defaults to GET when `method` is absent. TSS longstmt endpoints only accept POST, so a missing `method` causes a silent 404: panels display "No data", browser console shows `responseCodeFromServer: 404`, and the executed query string shows `curl -X 'GET'` instead of `curl -X 'POST'`.

**Always include `"method": "POST"` in every panel target's `url_options`**. Do not include `body_content_type` or `body_type` — the working pattern (verified on ModbusSim and virtual_0416 dashboards) does not use these keys.

Correct `url_options` shape (complete field list):

```json
"url_options": {
    "method": "POST",
    "data": "<JSON string of args body>",
    "body_form": [],
    "params": [],
    "headers": [],
    "body_graphql_query": "",
    "body_graphql_variables": "",
    "global_query_id": ""
}
```

**Diagnostic shortcut**: if all panels show "No data" after a fresh dashboard POST, check browser console `performance.getEntriesByType('resource')` for `/api/ds/query` entries with `responseStatus: 400`. Then run the same query via Grafana datasource proxy (`POST /api/datasources/proxy/uid/<ds_uid>/api/v1/query/<uri>`) — if the proxy returns data but ds/query returns 400, the issue is the missing `method: "POST"` in `url_options`.

## INTERVAL sizing

`INTERVAL(10s)` means 10-second aggregation windows using LAST() function. For 50ms raw data, 10s interval reduces 200 points to 1 per prop per interval. Size the interval based on the dashboard time window — aim for ~30 data points across the visible range.

For user-specified sampling rates (e.g., "10s"), use `INTERVAL(10s)` directly.

## Multiple longstmts for full coverage

When a tm_code has props across DOUBLE/INT/BOOL tables, create one longstmt per table. Use `gen-table-name` with each `data_type` (DOUBLE, INT, BOOL) to discover the actual `main_table` names, then create one longstmt per table. Each Grafana panel references the appropriate longstmt URI based on which td_data_type its props belong to.

## Data source routing

InfluxDB and TDengine may both be configured in tsdb-memory.json, but only one may have actual data for a given model. The `connect-ping` succeeding only means the connection works, not that data exists. **Data routing is per-model, not per-system** — one model's data may be in InfluxDB while another's is in TDengine, even when both databases list the same `thinglink_refs`.

### Agent-memory credentials may be stale — verify against TSS config

The `tsdb-memory.json` file may contain outdated bucket names, tokens, or URLs for InfluxDB. Before concluding that InfluxDB has no data for a model, verify the actual configured credentials:

```bash
curl -s -u "admin:<tss_password>" "http://<tss_host>:<tss_port>/api/v1/config/tsdb" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for ds in data.get('data', []):
    if ds.get('tds_type') == 'influxdb-v2':
        content = json.loads(ds.get('tds_content', '{}'))
        print(f\"bucket={content.get('bucket')}, token={content.get('token','')[:20]}...\")
"
```

If the bucket or token in the TSS config differs from `tsdb-memory.json`, update the memory file and retry the InfluxDB query with the correct bucket. Common staleness pattern: memory says `bucket: "dedge"` but actual config uses a date-based bucket like `bucket: "20260601"`.

### HSL gateway type flattening in InfluxDB

When data flows through the HSL edge gateway (tl_code=`hsl`), the gateway may write INT, BIGINT, and DOUBLE props all with `data_type: "DOUBLE"` into the `dedge_DOUBLE` measurement. Only BOOL props go to `dedge_BOOL`. This means:

- A single InfluxDB longstmt with a `measurement` parameter can serve all numeric types (DOUBLE, INT, BIGINT) by passing `measurement: "dedge_DOUBLE"` or `measurement: "dedge_BOOL"`.
- The `dedge_BIGINT` supertable may not exist in TDengine at all — this is normal when the model's data goes to InfluxDB.
- When counting props by type in InfluxDB, group by the `data_type` tag to discover the actual type distribution (e.g. 150 props all tagged `data_type: "DOUBLE"` even though Cloud lists 50 INT + 50 BIGINT + 50 DOUBLE).

### Cloud prop_code vs InfluxDB prop tag mismatch

Cloud API prop_code values (from `dedge cloud tm prop ls`) may not match the actual `prop` tag values stored in InfluxDB. For example, Cloud may list `HR300_LONG_0` as the first BIGINT prop, but InfluxDB stores it as `HR350_LONG_0` (reflecting the actual Modbus register address). **Always verify prop names against the actual time-series database** using a `distinct(column: "prop")` Flux query, rather than trusting Cloud prop_code values for dashboard transform regex patterns.

### Data flow verification via MQTT

When both TDengine and InfluxDB show 0 rows for a model but the HSL gateway reports the device as alive (`dedge hsl read value <device>` succeeds), verify that data is actually being published to MQTT:

```python
# Minimal MQTT subscriber to check if thingmodel/<tl_code>/<tm_code> topic has data
import socket, struct, time
# Connect to EMQX broker, subscribe to "thingmodel/<tl_code>/<tm_code>", read for 3-5 seconds
```

The HSL gateway publishes to topic `thingmodel/<tl_code>/<tm_code>` with payload format `{"version":"mqttjsonv2","ts":<ms>,"tags":{"tm_code":"<code>","tl_code":"<tl_code>"},"data":[{"ts":<ms>,"prop":"<name>","val":<value>,...}]}`. If MQTT data is flowing but TSDB has no data, the ts-singleserver subscription or write pipeline may be broken — report to user.

### Virtual device models (VGATE_VIRTUAL_TM)

Virtual device models (`tm_type_code=VIRTUAL_DEVICE`, `tm_dri_code=VGATE_VIRTUAL_TM`) have props that alias to another model's props via `add_cfg_frm_content` (JSON with `alias_tm_code` and `alias_prop_code`). Despite the aliasing, the time-series data is stored in InfluxDB under the **virtual model's own `tm_code`**, not the aliased model's `tm_code`. The `tl_code` tag in InfluxDB reflects the data link that carries the virtual model's data (e.g. `test0212`).

Key implication for data discovery: when probing for a virtual model's data, always use the virtual model's own `tm_code` in the Flux filter, not the aliased model's code. The aliased model's data may not exist or may be in a different time range.

### tmagg query vs Flux stmt-query discrepancy on InfluxDB

The `dedge ts-singleserver tsdb query` (tmagg format) may return `rowCount=0` or `rowCount=None` with empty columns for time ranges where data actually exists, while Flux `stmt-query` with the same time range and `tm_code` filter successfully returns rows. This discrepancy has been observed with virtual device models and with wide time ranges (7+ days).

When `tmagg query` returns 0 rows on InfluxDB but you suspect data exists (e.g. `gen-table-name` succeeded, the model is enabled, or the thinglink is active), **always verify with a Flux `stmt-query`** using an explicit `filter(fn: (r) => r["tm_code"] == "<code>")` clause before concluding the model has no data. The Flux query is more reliable for exploratory probing on InfluxDB.

### Flux aggregateWindow longstmt for high-frequency data

For high-frequency data (50-100ms sampling), a plain `sort` + `limit(n: 500000)` Flux longstmt can return millions of rows over hours, causing Grafana rendering lag and TSS cache pressure. Add `aggregateWindow` with a parameterized `interval` to downsample at the TSS layer:

```
from(bucket: params.bucket)
  |> range(start: time(v: params.start), stop: time(v: params.stop))
  |> filter(fn: (r) => r["_measurement"] == params.measurement)
  |> filter(fn: (r) => r["tm_code"] == params.tm_code)
  |> filter(fn: (r) => r["_field"] == "val")
  |> filter(fn: (r) => contains(value: r.prop, set: params.props))
  |> aggregateWindow(every: duration(v: params.interval), fn: mean, createEmpty: false)
  |> sort(columns: ["_time"])
  |> limit(n: 500000)
```

对应 count_stmt 模板（共享同一管道，末尾改为 count）：
```
from(bucket: params.bucket)
  |> range(start: time(v: params.start), stop: time(v: params.stop))
  |> filter(fn: (r) => r["_measurement"] == params.measurement)
  |> filter(fn: (r) => r["tm_code"] == params.tm_code)
  |> filter(fn: (r) => r["_field"] == "val")
  |> filter(fn: (r) => contains(value: r.prop, set: params.props))
  |> aggregateWindow(every: duration(v: params.interval), fn: mean, createEmpty: false)
  |> count()
```

The `schema_json.required` should include `interval` and `props` alongside `bucket`, `start`, `stop`, `measurement`, `tm_code`. Grafana panels pass the interval as a string like `"10s"` and `props` as a string array like `["VOL","CUR1"]`. This approach keeps the total row count around 30 points per prop per visible window, matching the grafana-dashboard skill's default sampling guidance.

Note: the `filter` uses `tm_code` (not `tl_code`) when the model's data is the only filter needed. The `tl_code` filter is optional and should only be added when multiple thinglinks write to the same measurement for the same `tm_code` (rare).

### BOOL aggregateWindow must use `last`, not `mean`

InfluxDB Flux rejects `mean` aggregation on boolean fields:

```
code: 4, msg: "执行查询失败: invalid: unsupported input type for mean aggregate: boolean"
```

When creating a Flux longstmt for a BOOL measurement (e.g. `dedge_BOOL`), use `fn: last` in `aggregateWindow`:

```
from(bucket: params.bucket)
  |> range(start: time(v: params.start), stop: time(v: params.stop))
  |> filter(fn: (r) => r["_measurement"] == params.measurement)
  |> filter(fn: (r) => r["tl_code"] == params.tl_code)
  |> filter(fn: (r) => r["tm_code"] == "<tm_code>")
  |> filter(fn: (r) => r["_field"] == "val")
  |> filter(fn: (r) => contains(value: r.prop, set: params.props))
  |> aggregateWindow(every: 10s, fn: last, createEmpty: false)
  |> sort(columns: ["_time"])
  |> limit(n: 500000)
```

对应 count_stmt 模板（共享同一管道，末尾改为 count）：
```
from(bucket: params.bucket)
  |> range(start: time(v: params.start), stop: time(v: params.stop))
  |> filter(fn: (r) => r["_measurement"] == params.measurement)
  |> filter(fn: (r) => r["tl_code"] == params.tl_code)
  |> filter(fn: (r) => r["tm_code"] == "<tm_code>")
  |> filter(fn: (r) => r["_field"] == "val")
  |> filter(fn: (r) => contains(value: r.prop, set: params.props))
  |> aggregateWindow(every: 10s, fn: last, createEmpty: false)
  |> count()
```

This means a model with DOUBLE/INT/BOOL data types needs **two** longstmt entries when using `aggregateWindow`: one with `fn: mean` (for DOUBLE + INT, which share the same template hash and get the same URI) and one with `fn: last` (for BOOL, which gets a different URI due to the different template string).

### Same template + parameterized measurement = shared longstmt URI

When a Flux template uses `params.measurement` (not a hardcoded measurement name), TSS computes the `stmt_hash` from the template string only — not from the runtime argument values. This means:

- A single longstmt with `measurement` as a parameter serves ALL measurements of the same aggregation type.
- DOUBLE and INT measurements sharing an identical `fn: mean` template get the **same `uri_segment`** (same `stmt_hash16`).
- BOOL measurements using `fn: last` get a different `uri_segment` (different template string).

Grafana panels differentiate by passing different `args.measurement` values in `url_options.data` — `"dedge_DOUBLE"` vs `"dedge_INT"` vs `"dedge_BOOL"`. TSS caches per-args-hash, so each measurement still gets its own cache entry despite sharing a URI.

Practical implication: for a model with DOUBLE + INT + BOOL data, you only need to create **2 longstmt entries** (one mean-template, one last-template), not 3.

### Systematic data source discovery procedure

When a model has 0 rows in TDengine (verified via COUNT with time range + tm_code filter), follow this procedure:

1. **Check agent-memory for InfluxDB credentials**, then **verify against TSS config** (see above).
2. **Query InfluxDB with the correct bucket**: `from(bucket: "<actual_bucket>") |> range(...) |> filter(fn: (r) => r.tm_code == "<code>") |> count()`.
3. **If InfluxDB also returns 0**: Check MQTT data flow (see above) to determine if the issue is collection (device/gateway) or persistence (ts-singleserver write).
4. **If InfluxDB has data**: Create InfluxDB longstmts (Flux-based, per `datacenter-agent-cloud-tss-query` skill) instead of TDengine longstmts. Use the `measurement` parameter approach so one longstmt serves both DOUBLE and BOOL measurements.

### Systematic data inventory (which models actually have data)

When a user asks "which thing models have real data" or you need to determine data availability across all models and data sources, use this proven procedure:

**Step 1 — List all models**: `dedge cloud tm tree --json` → recursively extract all `tm_code` values from `model_attributes`. Typical result: 50-70 models.

**Step 2 — InfluxDB measurement scan**: Use Flux `last()` grouped by `_measurement` to list all measurements with data. The `import "influxdata/influxdb/schema"` statement is rejected by TSS as non-readonly. Use this pattern instead:

```
from(bucket: params.bucket)
  |> range(start: time(v: params.start), stop: time(v: params.stop))
  |> group(columns: ["_measurement"])
  |> last()
  |> keep(columns: ["_measurement", "_time"])
  |> filter(fn: (r) => not (r._measurement =~ /^(go_|boltdb_|qc_|storage_|task_|http_|query_|service_|influxdb_)/))
```

- Time ranges >30d cause TSS timeout. Use 7d for recent data, then a wider range (180d+) only with the internal-metric filter active.
- The `filter` line is critical — without it, InfluxDB returns 100+ internal monitoring measurements (go_*, boltdb_*, storage_*, etc.) that drown out device data.
- Device measurements in InfluxDB typically follow patterns like `<tm_code_lowercase>_<datatype>_<hash>` or `tmagg-influx-<id>_<datatype>_<hash>`.
- To also discover `tl_code` tags, group by both `_measurement` and `tl_code` (grouping by `tl_code` alone causes schema collision between float and boolean measurements).

**Step 3 — TDengine per-model probe**: Use `dedge ts-singleserver tsdb query` (NOT stmt-query) with the tmagg format. The `tmagg` object requires `tm_code`, `prop`, and `data_type` (not `td_data_type`). To check a model:

```json
{
  "tmagg": {"tm_code": "<code>", "prop": "<any_prop>", "data_type": "DOUBLE"},
  "start_time": "2026-07-10T02:24:00Z",
  "end_time": "2026-07-10T02:25:00Z"
}
```

- Get a valid `prop` for each model first via `dedge cloud tm prop ls -tmCode <code> -pageSize 5`.
- **Table existence detection**: Even when `rowCount=0`, the `meta.tableName` field in the response reveals the actual TDengine table name (e.g. `dadevice-coll-1_double_4e7cde5f`). If `tableName` is present, the table exists but has no data in that time window. If the response contains error `[0x2603] Fail to get table info, error: Table does not exist`, the model has no TDengine table at all.
- **Memory exhaustion = data exists**: Error `[0x73a] Query memory exhausted` means the table has a large amount of data. Narrow the time window to 1 minute or less.
- Always use 1-minute windows for probing — wider windows (24h+) on high-frequency tables (50ms sampling) will exhaust TDengine query memory.
- `stmt-query` with TDengine SQL (e.g. `SELECT COUNT(*) FROM ...`) returns `[0x118] Invalid parameters` — the stmt-query wrapper does not support TDengine SQL. Use the `query` command with tmagg format instead.

**Step 4 — Data freshness pinpointing**: To find the exact last data point for a model, binary-search by 1-minute windows. Start at hour boundaries, then narrow to minute granularity. A model with ~620 rows/minute at 50ms sampling confirms continuous high-frequency data flow. Convert UTC to Beijing time (UTC+8) for user-facing reporting.

**Step 5 — Cross-reference with Cloud thinglinks**: `dedge cloud tl ls --json` lists all data links (`tl_code`). Each model's data carries a `tl_code` tag. Models without active thinglinks typically have no data flowing.

See `references/data-inventory-procedure.md` for a condensed reproduction recipe with exact commands. See `references/influxdb-data-source-discovery.md` for the full procedure when TDengine has no data but InfluxDB might (including MQTT verification, credential discovery, and HSL type flattening). See `references/virtual-device-model-routing.md` for virtual device model (VGATE_VIRTUAL_TM) data routing, tmagg vs Flux discrepancy, and aggregateWindow longstmt patterns.

## Grafana 看板无数据诊断

当用户报告"Grafana 中没有数据"时，按以下诊断链逐层排除。每层只花一个请求，定位到根因即停。

### 诊断链（从外到内）

1. **Grafana + 后端健康**：`curl` Grafana `/api/health`（期望 200）和后端 `/api/health`。两者都正常则排除基础设施故障。
2. **Infinity 数据源健康**：`GET /api/datasources/uid/<ds_uid>/health`（期望 `status: OK`）。不正常则查密码/网络（见 grafana-dashboard 技能"看板全空白"节）。
3. **Grafana ds/query API**：用看板面板的 target 构造 `POST /api/ds/query` 请求。检查返回的 `frames`：
   - `frames[0].schema.fields` 为空 → Infinity 未拿到任何数据，TSS 返回了空响应
   - `frames[0].data.values` 非空 → 数据通路正常，问题在浏览器渲染（等更久或查 Infinity 列映射）
   - 如果 ds/query 返回 404（Infinity 数据源在 ds/query 端点的 URL 拼接行为与面板内不同），改用 **datasource proxy** 验证：`POST /api/datasources/proxy/uid/<infinity_ds_uid>/api/v1/query/<uri_segment>`，body `{"args":{"1":"<from>","2":"<to>"}}`。proxy 路径更接近 Infinity 面板实际请求路径，且 404 风险更低。
4. **TSS longstmt 直接查询**（绕过 Grafana）：`POST {tss.url}/api/v1/query/{uri_segment}`，body `{"args":{"1":"<from>","2":"<to>"}}`。检查 `data.meta.rowCount` 和 `data.columns`：
   - `rowCount=0, columns=[]` → 时间窗内无数据（表可能不存在或数据已停止）
   - `rowCount=0, columns=[...]` → 表存在但该时间窗无数据，需要扩大时间范围
   - `rowCount>0, columns=[...]` → TSS 正常，问题在 Grafana→TSS 链路（密码/网络/Infinity 配置）
5. **数据新鲜度定位**：用 longstmt 对多个时间窗做指数扩展搜索，定位最后一条数据的时间戳。用指数扩展窗口（1h → 6h → 24h → 3d → 7d → 14d → 30d）快速定位数据边界，找到有数据的最大窗口后再在该窗口内用分钟粒度缩小。线性逐小时扫描在数据停止数天时会产生过多无用请求。注意：TDengine longstmt 查询大范围（7天+）且 prop 数多（60+）× INTERVAL(10s) 时可能超时（curl 30s+），遇到超时缩小窗口重试，不要当作查询错误。
6. **采集链路排查**（超出 agent 职责时告知用户）：
   - `dedge cloud tl ls --json` 查看数据链路是否存在
   - `dedge cloud tc ls --json` 查看组件配置（HSL 组件地址在 `tc_address`，凭据在 `tc_cfg_content`）
   - `dedge hsl login <tc_address> <user> <pass>` → `dedge hsl device ls` → `dedge hsl read value <device>`：直接从 HSL 网关读取实时值，确认设备和本地采集是否正常。如果 `read value` 成功但 TDengine 无数据，问题在 HSL→Cloud MQTT 上报链路。
   - HSL MQTT 连接失败常见错误：`802_ErrorNotRegistered: 读取CONNACK失败: EOF`

### Prometheus 看板的数据可用性验证

Prometheus 支持的看板（如系统监控、PProf 监控）不经过 TSS longstmt，Infinity 也不参与。它们的 panel target 中是 PromQL 表达式（`expr` 字段），数据源是 Grafana 直接配置的 Prometheus 数据源。

验证 Prometheus 看板是否有数据，使用 Grafana `POST /api/ds/query` API：

```bash
curl -s -m 10 -X POST '<grafana_url>/api/ds/query' \
  -H 'Authorization: Bearer <grafana_token>' \
  -H 'Content-Type: application/json' \
  -d '{"queries":[{"refId":"A","datasource":{"uid":"<prometheus_ds_uid>"},"expr":"<metric_name>","instant":true,"range":false}],"from":"now-5m","to":"now"}'
```

检查返回的 `results.A.frames[].data.values` 是否非空。如果 `values` 为空或 `frames` 为空数组，说明该 Prometheus 数据源在近 5 分钟内没有该指标的数据。

**注意**：Prometheus 看板通常使用 `${datasource}` 模板变量，需要先从看板 JSON 的 `templating.list` 中找到 `type=datasource` 的变量，读取其 `current.value` 得到实际数据源 UID。一个 Grafana 实例可能配置了多个 Prometheus 数据源（不同 host:port），看板实际使用哪一个由模板变量决定。

### 关键判别信号

| TSS 响应模式 | 含义 | 下一步 |
|---|---|---|
| `rowCount=0, columns=[]` (所有时间窗) | 表不存在或数据从未写入此时间范围 | 扩大到更早时间窗测试；确认表名正确 |
| `rowCount=0, columns=[]` (近期) 但 `rowCount>0` (历史) | **数据采集管道停止** 或 **表名迁移** | 先定位停止时间点；再用 `gen-table-name` 检查当前表名是否变化（旧表可能仍在 `SHOW STABLES` 中但不再接收数据）；检查共享超表 `dedge_DOUBLE/INT/BOOL` 中 `tm_code` 过滤后是否有新数据 |
| `rowCount=0, columns=[...]` | 表存在，查询正常，只是该窗口无数据 | 缩小或移动时间窗 |
| `rowCount>0` | TSS 层正常 | 问题在 Grafana 侧（密码/Infinity 配置/列映射） |
| Prometheus ds/query `frames` 为空 | Prometheus 数据源无该指标数据 | 检查 Prometheus target 是否在线；检查指标名是否正确 |

**最常见的根因**：不是 Grafana 配置问题，而是 TDengine 中数据停止写入。看板默认时间范围 `now-5m`，如果数据采集在数小时/数天前停止，所有面板自然空白。先做第 5 步数据新鲜度定位，再决定是否需要深入 Grafana 配置排查。

## 多看板数据可用性审计

当用户要求"删除没有数据的看板"或"只保留有数据的看板"时，需要对 catalog 中的每个看板逐一验证数据可用性。不同看板可能使用不同的数据源类型，验证方法也不同。

### 审计流程

1. **读取 catalog**，获取所有看板的 `dashboardUid`。
2. **从 Grafana 拉取每个看板的完整 JSON**（`GET /api/dashboards/uid/<uid>`），提取每个 panel 的 target 信息：
   - Infinity target（有 `url` 字段指向 `/api/v1/query/<uri>`）→ TSS longstmt 数据源
   - Prometheus target（有 `expr` 字段）→ Prometheus 数据源
   - 无 target 或 `${datasource}` 模板变量 → 需要从 `templating.list` 解析实际数据源
3. **按数据源类型分组验证**：
   - TSS longstmt：直接 `POST {tss_url}/api/v1/query/{uri}` 查询最近 5 分钟。注意从看板 JSON 中提取正确的 `url_options.data` 参数格式——不同 longstmt 使用不同的参数名（如 `"1"/"2"` 或 `"start"/"stop"/"bucket"/"measurement"/"tm_code"`）。用错误参数名会返回 `code: 3, msg: "args schema validate failed: invalid argument"`。
   - Prometheus：`POST /api/ds/query` 用看板 panel 中的 PromQL 表达式做 instant 查询。
4. **对 0 行结果扩大时间范围**：TSS longstmt 先试 5 分钟，再扩大到 1h、24h，定位数据停止时间。Prometheus 扩大到 1h。
5. **汇总结果**：列出每个看板的数据状态（有数据 / 无数据 / 数据停止 N 小时），供用户确认后删除。

### 看板删除流程

确认要删除的看板后：

1. **删除公共看板分享**：`DELETE /api/dashboards/uid/<uid>/public-dashboards`（可能返回 `Not found`，说明之前未创建公共分享，可忽略）。
2. **删除看板本身**：`DELETE /api/dashboards/uid/<uid>`。
3. **删除空文件夹**：如果被删除的看板是某个 Grafana 文件夹中唯一的看板，删除该文件夹（`DELETE /api/folders/<folder_uid>`）。
4. **更新 catalog**：从 `dashboards` 数组中移除被删看板；从 `tree` 中移除对应节点；如果目录节点变为空，移除整个目录节点。
5. **重新扁平化 tree**：如果删除后所有剩余看板都在 Grafana root 目录，tree 必须为扁平结构（无 directory 节点），遵循 catalog-maintenance 规则 16。
6. **更新 currentView**：如果 currentView 指向被删看板，改为指向一个仍有数据的看板。
7. **验证并通知**：通过 backend Pydantic model 校验 catalog，POST current-view，POST notify/frontend-refresh。

## HTTP query response codes

When executing longstmts via HTTP `POST /api/v1/query/{uri_segment}`:

- `code: 0` — success, check `data.rows` for actual results. However, `code: 0` with `columns=[]` and `rows=[]` (completely empty TypeFrame) means the TDengine table returned no rows for the time window — this is subtly different from `code: 3`. With `code: 0 + empty columns`, no aggregation buckets were produced at all (data absent from the entire window). With `code: 3`, the query executed but TDengine reported 0 rows explicitly. In both cases the action is the same: widen the time range or check data freshness.
- `code: 3` (two distinct sub-cases — always check `status` and `msg`):
  - **Schema validation failure**: `status: "invalid_input"`, `msg: "args schema validate failed: invalid argument"`. The args object is missing required fields or uses wrong parameter names. **Do not widen the time range** — instead, inspect the longstmt's actual `schema_json` and `stmt_template` via `longstmt ls --json` (or `longstmt get -id <id>`) to find the correct required parameter names and types. The `schema_json` field is a JSON string; parse it to read the `required` array and `properties` object. Common cause: catalog description or memory says the longstmt uses `tl_code` as a filter, but the actual template uses `tm_code` (or vice versa), or an `interval` parameter is required but not passed. The longstmt's own schema is the authority — never assume parameter names from catalog descriptions or session memory.
  - **Zero rows**: no `status: "invalid_input"` field. The query executed successfully but the time window contains no data. Widen the time range or check data freshness. Distinct from connection failures (which surface as HTTP-level errors) and from Flux-on-TDengine (`code: 4`).
  - **count_stmt threshold exceeded**: `msg: "count_stmt result <N> exceeds max allowed 1000: invalid argument"`. The count_stmt returned more than 1000 rows for the given time window. **This is a positive data-existence signal** — `<N>` tells you exactly how many rows exist in that window. Use it during binary search to narrow the window until count < 1000. Do NOT widen the time range when you see this; narrow it instead. See "count_stmt 1000-row threshold" section for strategies.
- `code: 8` — **HTTP authentication failure**: `status: "permission_expired"`, `msg: "unauthorized"`. The TSS HTTP API requires HTTP basic auth on every request. `dedge tss login` configures the CLI session but does NOT configure HTTP-level auth. **Fix**: add `-u "admin:<tss_password>"` to every curl call to the TSS HTTP API. The CLI (`dedge tss longstmt exec --data '{...}'`) works without explicit auth because it uses the login session. If the HTTP API returns `code: 8`, switch to CLI (`dedge tss longstmt exec --uri <uri> --data '{"args":{...}}' --json`) or add basic auth to the curl command.

## Grafana transform chains for multi-prop panels

When a dashboard panel needs to display multiple props from a single longstmt target (e.g. a bargauge showing 50 FAULT_CODE values, or a table listing 300 ADD register values), the transform chain matters:

### Multi-prop bargauge / table: `filterByValue → partitionByValues → reduce`

```json
"transformations": [
  {"id": "filterByValue", "options": {
    "filters": [{"fieldName": "Prop", "config": {"id": "regex", "options": {"value": "^FAULT_CODE[0-9]*$"}}}],
    "type": "include", "match": "any"
  }},
  {"id": "partitionByValues", "options": {"fields": ["Prop"]}},
  {"id": "reduce", "options": {"reducers": ["lastNotNull"]}}
]
```

Why: `partitionByValues` splits the single Infinity table into one frame per prop value. `reduce(lastNotNull)` then collapses each frame to its latest value. Without `partitionByValues`, `reduce` sees all props as a single frame and outputs only one row/value.

### Common failure: using `organize → reduce` for multi-prop panels

The stat panel chain `filterByValue → organize → reduce` works for **single-prop** panels (where `organize` excludes non-numeric columns so `reduce` targets one value). But for **multi-prop** bargauge/table panels:

- **bargauge**: displays "No data" — `organize` + `reduce` collapse all rows into one scalar, and bargauge can't render it.
- **table**: displays only 1 row — all prop values are reduced to a single `lastNotNull` instead of one-per-prop.

### Transform chain summary by panel purpose

| Panel purpose | Transform chain |
|---|---|
| Single-prop stat (one latest value) | `filterByValue → organize → reduce` |
| Multi-prop timeseries (many lines) | `filterByValue → partitionByValues → prepareTimeSeries` |
| Multi-prop bargauge (many latest values) | `filterByValue → partitionByValues → reduce` |
| Multi-prop table (many latest values) | `filterByValue → partitionByValues → reduce` |
| Multi-prop state-timeline (BOOL) | `filterByValue → partitionByValues → prepareTimeSeries` |

### Boolean values in state-timeline panels

For BOOL data consumed via a `fn: last` longstmt, the `_value` column contains `true`/`false` booleans. Grafana `state-timeline` panels handle boolean values natively — no special column mapping is needed beyond the standard `_time`/`_value`/`prop` columns. The `partitionByValues → prepareTimeSeries` chain splits each BOOL prop into its own frame, and the state-timeline renders `true`/`false` as colored segments.

## Reusing existing longstmts for new dashboards

Before creating a new longstmt, check `longstmt ls` for existing entries covering the same `main_table`. A single longstmt returns ALL props for its measurement (via `PARTITION BY prop`), so a new dashboard focused on a subset of props (e.g. only CUR and TEMP from a DOUBLE table that also has VOL/SOC/SOH) can reuse the same longstmt URI. The Grafana Infinity panel's transform chain (`filterByValue` with regex) handles prop filtering on the client side. Only create a new longstmt when:
- The target props belong to a different `td_data_type` table (DOUBLE vs INT vs BOOL).
- A different `INTERVAL` is needed (e.g. 5s vs 10s).
- The existing longstmt is disabled.

## TSS 表名迁移：模型专属超表 → 共享类型超表

TSS 配置可能发生变更，导致数据写入目标从旧的模型专属超表迁移到新的共享类型超表。这是看板突然无数据的常见根因之一。

### 迁移模式

| 旧命名（模型专属） | 新命名（共享类型） | 说明 |
|---|---|---|
| `<tm_code_lowercase>_double_<hash>` | `dedge_DOUBLE` | 所有 DOUBLE 类型数据共享一个超表 |
| `<tm_code_lowercase>_int_<hash>` | `dedge_INT` | 所有 INT 类型数据共享一个超表 |
| `<tm_code_lowercase>_bool_<hash>` | `dedge_BOOL` | 所有 BOOL 类型数据共享一个超表 |

旧超表仍然存在于 `SHOW STABLES` 中，但不再接收新数据。新数据写入共享超表，通过 `tm_code` TAG 列区分不同物模型。

### 诊断方法

当 longstmt 查询返回 `rowCount=0` 但 `code=0` 时，不要立即断定数据采集停止。按以下步骤排查：

1. **检查旧表数据新鲜度**：`SELECT LAST(ts) FROM \`<old_main_table>\`` — 如果最后时间戳是数天前，数据可能已迁移。
2. **检查共享超表是否有新数据**：
   ```sql
   SELECT * FROM `dedge_DOUBLE` WHERE ts > '<recent_start>' AND ts < '<recent_end>' AND tm_code = '<tm_code>' AND prop = '<prop>' LIMIT 5
   ```
   如果共享超表有近期数据，说明数据已迁移。
3. **用 `gen-table-name` 确认当前表名**：
   ```json
   {"tmagg": {"tm_code": "<code>", "prop": "<prop>", "data_type": "DOUBLE", "tl_code": "<tl_code>"}}
   ```
   返回的 `main_table` 即为当前正确的超表名。

### 修复流程

确认数据已迁移到共享超表后：

1. **创建新 longstmt**，SQL 中用 `tm_code` TAG 过滤代替硬编码表名：
   ```sql
   SELECT prop, LAST(val), LAST(ts) FROM `dedge_DOUBLE` WHERE ts > ? AND ts < ? AND tm_code = '<tm_code>' PARTITION BY prop INTERVAL(10s)
   ```
2. 按「正确创建顺序」执行 stmt-query → longstmt up → HTTP 验证。
3. **更新 Grafana 看板**：将所有引用旧 longstmt URI 的面板 target URL 改为新 URI。
4. 通过 Grafana datasource proxy 验证数据返回：`POST /api/datasources/proxy/uid/<ds_uid>/api/v1/query/<new_uri>`。
5. 更新 catalog 元数据并通知前端。

### 批量迁移：多看板一次性更新

当一个物模型有多个看板（如电压与电量、全量数据看板、电流与温度监控），且它们引用了多个旧 longstmt URI（DOUBLE/INT/BOOL 各一个），手动逐面板修改容易遗漏。推荐批量流程：

1. **建立 URI 映射表**：`{旧URI: 新URI}`，覆盖所有需要替换的 longstmt。
2. **逐看板拉取最新 JSON → 批量替换 → 写回**（每次都重新 GET，不复用缓存）：
   ```python
   URI_MAP = {"<old_double>": "<new_double>", "<old_int>": "<new_int>", "<old_bool>": "<new_bool>"}
   for uid, name in dashboards_to_update:
       dash = fetch_dashboard(uid)   # GET /api/dashboards/uid/<uid>
       for panel in dash["panels"]:
           for target in panel["targets"]:
               for old_uri, new_uri in URI_MAP.items():
                   if old_uri in target["url"]:
                       target["url"] = target["url"].replace(old_uri, new_uri)
       post_dashboard(dash, overwrite=True)  # POST /api/dashboards/db
   ```
3. **写回后验证无旧 URI 残留**：重新拉取看板 JSON，遍历所有面板 target URL，确认旧 URI 全部消失。
4. **通过 Grafana datasource proxy 验证数据返回**：
   ```bash
   curl -s -X POST -H "Authorization: Bearer <grafana_token>" \
     -H "Content-Type: application/json" \
     -d '{"args":{"1":"<start_iso>","2":"<end_iso>"}}' \
     "<grafana_url>/api/datasources/proxy/uid/<infinity_ds_uid>/api/v1/query/<new_uri>"
   ```
   检查 `data.meta.rowCount > 0` 且 `data.rows` 中包含目标 prop。
5. **更新 catalog** 中受影响看板的 description（更新 longstmt URI 引用）和 updatedAt 字段。
6. **通知前端刷新**。

注意：同一物模型的多个看板可能引用不同的 longstmt URI 子集（如"电压与电量"只用 DOUBLE，"全量数据看板"用 DOUBLE+INT+BOOL），URI_MAP 应覆盖全部可能需要替换的 URI。

### 迁移后数据值异常检查

迁移到共享超表后，`val` 列的值可能出现异常模式。这是数据入库层问题，不是看板配置问题：

| 异常模式 | 典型值 | 含义 |
|---|---|---|
| DOUBLE val 看起来像毫秒时间戳 | `1785809783979`（≈当前时间） | 采集层把 ts 写入了 val 列 |
| INT val 出现大负数 | `-896610175` | 整数溢出或列映射错误 |
| BOOL val 正常 | `True`/`False` | BOOL 表通常不受影响 |

诊断方法：通过 Grafana proxy 查询新 longstmt，检查各 prop 的 `last(val)` 是否在合理量程内。如果 val 异常但 ts 正常（当前时间），说明看板配置已正确，问题在数据入库层，需告知用户。

### 迁移后验证：优先使用 Grafana datasource proxy

TSS HTTP API 直连验证（`POST {tss_url}/api/v1/query/{uri}`）只证明 longstmt 本身可用，不证明 Grafana Infinity 面板能拿到数据。**优先使用 Grafana datasource proxy 验证**，它测试的是 Infinity 实际请求路径：

```bash
curl -s -X POST -H "Authorization: Bearer <grafana_token>" \
  -H "Content-Type: application/json" \
  -d '{"args":{"1":"<start_iso>","2":"<end_iso>"}}' \
  "<grafana_url>/api/datasources/proxy/uid/<infinity_ds_uid>/api/v1/query/<new_uri>"
```

检查返回的 `data.meta.rowCount > 0` 且 `data.rows` 中包含目标 prop 即可确认数据通路完整。

### 关键注意

- 共享超表（如 `dedge_DOUBLE`）包含所有物模型的数据，查询时**必须**带 `tm_code` 过滤条件，否则会跨模型返回数据并导致超时。
- `gen-table-name` 返回的 `sub_table` 带有 `d` 前缀（如 `dtest0212_dadevice-coll-1_vol_67ea24`），这是 TDengine 子表命名约定，查询超表时不需要关心子表名。
- 迁移后旧 longstmt 不会自动失效（仍返回 `code:0`），只是返回空结果，容易误判为"数据采集停止"。
- 一个物模型的三个数据类型（DOUBLE/INT/BOOL）可能不在同一时间迁移。逐类型验证后再批量更新看板。

## stmt-query file format

The `stmt-query` CLI command expects a JSON file with three fields: `count_stmt` (a COUNT query that returns a small number, required), `stmt` (the SQL string, required), and `args` (object with numeric string keys, optional). Do NOT use `stmt_template` or `stmt` inside a nested object — the top-level keys are `count_stmt`, `stmt`, and `args`:

```json
{
  "count_stmt": "SELECT COUNT(*) FROM (SELECT COUNT(*) FROM `dedge_DOUBLE` WHERE ts > ? AND ts < ? AND tm_code = '<tm_code>' AND prop IN (?) PARTITION BY prop INTERVAL(10s))",
  "stmt": "SELECT prop, LAST(val), LAST(ts) FROM `dedge_DOUBLE` WHERE ts > ? AND ts < ? AND tm_code = '<tm_code>' AND prop IN (?) PARTITION BY prop INTERVAL(10s)",
  "args": {"1": "2026-08-11T03:22:00Z", "2": "2026-08-11T03:27:00Z", "3": "CUR1,CUR2,CUR3"}
}
```

注意: `count_stmt` 在 CLI schema 中是 required 字段，不是可选建议。缺失 `count_stmt` 会被 schema 校验直接拒绝，命令不会执行。`count_stmt` 返回的数值需足够小才放行 `stmt`——阈值由后端控制。

Incorrect field names (`stmt_template`, `sql`, `flux`) or array-format args (`["start", "stop"]`) return `code: 3, msg: "invalid argument"` with no further explanation. Verify with `dedge tss tsdb stmt-query --schema-input` if the format changes.

### Always use `--file`, never `--data` for stmt-query with SQL string literals

The CLI accepts both `--data '<json>'` and `--file <path>`, but **`--data` is unsafe when the SQL template contains single-quoted string literals** (e.g. `tm_code = 'virtual_0416'`). Python's `json.dumps()` does not escape single quotes inside JSON string values, so the resulting JSON contains raw `'` characters. When this JSON is passed as a shell argument wrapped in single quotes (e.g. `--data '{"stmt":"... tm_code = \'virtual_0416\' ..."}'`), the shell's single-quote wrapping breaks at the first `'` inside the SQL, causing the SQL to be parsed incorrectly. Symptoms include:

- `code: 4, msg: "执行查询失败: [0x2602] Invalid column name: virtual_0416"` — the unquoted `virtual_0416` is treated as a column identifier instead of a string literal.
- `code: 4, msg: "执行查询失败: [0x2600] syntax error near ..."` — the SQL is truncated or mangled.

**Always write the JSON to a temp file and use `--file <path>`** for stmt-query (and longstmt up) when the SQL contains any single-quoted values. This avoids shell quoting issues entirely.

## query vs stmt-query: critical difference for tm_code filtering

The `query` command (tmagg format) does NOT filter by `tm_code` by default — it returns ALL data from the target supertable across all models. However, the `query` command DOES support a `filters` parameter at the top level of the request body that filters by tag columns including `tm_code`:

```json
{
  "tmagg": {"tm_code": "<code>", "prop": "<prop>", "data_type": "INT"},
  "start_time": "2026-08-11T08:30:00Z",
  "end_time": "2026-08-11T08:35:00Z",
  "filters": {"tm_code": "<code>"}
}
```

Without `filters`, a query on `dedge_INT` returns all models' data (e.g. 1.3M rows in 5 minutes across all models). With `filters: {"tm_code": "virtual_0416"}`, the same query returns only that model's data (e.g. 12K rows for 4 props at 100ms sampling).

The `stmt-query` command with an explicit `WHERE tm_code = '<code>'` clause in the SQL also filters correctly. Both approaches work; `stmt-query` is preferred for longstmt creation (it registers the success sample), while `query` with `filters` is useful for quick data probes and COUNT-style checks.

### Dashboard creation: never use `query`, always use `stmt-query` + `longstmt`

**In dashboard creation workflows, always use `stmt-query` and `longstmt`. Never use `tsdb query` (tmagg format).** A historical session audit of 7 successful dashboard creation sessions confirmed that none of them ever used `tsdb query` — all completed via `longstmt` (some with `stmt-query` for sample registration and `gen-table-name` for table discovery).

Using `tsdb query` in dashboard workflows risks:
- Full table scans when `filters` parameter is omitted (260K+ rows pulled in a single call)
- No `stmt_success` sample registration, blocking subsequent `longstmt up`
- Inconsistent query semantics vs the longstmt that Grafana panels actually consume

**Pitfall**: the `datacenter-agent-cloud-tss-query` skill's TSS 规划 step 3 says "简单单点查询优先使用 tmagg query" — this is reasonable for one-off single-value probes, but must NOT be extended to dashboard creation. Dashboard queries always go through the `stmt-query → longstmt up → longstmt exec` pipeline.

## 禁止绕过 ts-singleserver 直连数据库

All time-series queries must go through `dedge ts-singleserver` CLI or its HTTP API (port 18081). Never directly curl database ports (e.g. InfluxDB 8086, TDengine 6030) to execute queries. ts-singleserver is the sole permitted query entry point — it handles authentication, caching, and safety limits. Bypassing the service to connect directly to the database skips all these protections and violates the system's security boundary.

If ts-singleserver returns unexpected results (0 rows, errors), the fix is to correct the parameters (tds_code, bucket, time range, filters) passed to ts-singleserver — not to bypass it and query the database directly.

## Catalog-first data source resolution

Before planning TSS queries for a model, always check if the dashboard catalog (`dedge-datacenter/catalog/dashboard-catalog.json`) already has an entry for that model. If it does, extract the data source information from the catalog entry first:
- `tds_code` (which database: TDengine_network_server vs InfluxDB_network_server)
- `bucket` (InfluxDB bucket name — may differ from the default "dedge")
- `longstmt URI` (existing pre-registered query)
- `measurement` or `main_table` name
- `tl_code` / `tm_code`

Only when the catalog lacks this information or it's outdated should you fall back to full exploration (gen-table-name, connect-ping, etc.).

**Critical pitfall**: Skipping the catalog and assuming a default data source (e.g. always querying TDengine first) leads to wasted effort querying the wrong database. In one session, the agent spent 30+ queries on TDengine and InfluxDB bucket "dedge" before discovering the catalog already recorded `tds_code=InfluxDB_network_server, bucket=20260601` — a completely different bucket that had the data all along.

The catalog entry's `description` field often contains the data source routing information in free text. Search for keywords like "bucket", "tds_code", "InfluxDB", "TDengine", "longstmt" within the description.

## BIGINT supertable may not exist

Not all TDengine type supertables are guaranteed to exist. `SHOW STABLES` is the authoritative check. If `gen-table-name` returns `main_table=dedge_BIGINT` but `stmt-query` on that table returns `[0x2603] Table does not exist`, the supertable has never been created (no data was ever written for that type). This means the corresponding Cloud `td_data_type=LONG` props have no time-series storage yet — the data pipeline must be fixed before a dashboard can display them.

When creating longstmts for a model with multiple td_data_types, check each type independently. If BIGINT doesn't exist, skip it and create longstmts only for the types whose supertables do exist (typically DOUBLE, INT, BOOL). The dashboard can still be built and will display all available data types — LONG props simply won't have data until the pipeline is fixed. Do not block the entire dashboard on a missing BIGINT table.

## gen-table-name always succeeds — it is NOT an existence check

`gen-table-name` generates table names purely from naming conventions (tm_code + tl_code + data_type + prop hash). It returns `code: 0` with valid-looking `main_table` and `sub_table` values even when:
- The tm_code does not exist in Cloud (verified via `dedge cloud tm ls --tm_code <code>`)
- No subtable has ever been created in TDengine for this model
- No data has ever been written

**Never interpret a successful gen-table-name response as evidence that data exists.** It only tells you what the table name WOULD be if data were written. Always follow up with an actual data probe (stmt-query with time range + tm_code filter, or `query` with tmagg format) to confirm data presence.

## "Table does not exist" on shared supertables with tm_code filter

When querying a shared supertable (e.g. `dedge_DOUBLE`) that DOES exist (confirmed via `SHOW STABLES`) with `WHERE tm_code = '<code>'`, TDengine may still return `[0x2603] Fail to get table info, error: Table does not exist` (code: 4). This means no SUBTABLE exists for that specific tm_code within the supertable — the model has never had data written to this supertable. This is distinct from the supertable itself being missing.

Diagnostic implication: `SHOW STABLES` confirms the supertable exists, but only a data probe with `WHERE tm_code = '<code>'` confirms whether a specific model has subtables. Both checks are needed when verifying a new model's data availability.

## information_schema.ins_tables: the reliable subtable search method

`DESCRIBE dedge.dedge_DOUBLE` via stmt-query may fail with "Table does not exist" even when `SHOW STABLES` confirms the supertable exists and `information_schema.ins_tables` lists subtables under it. This is a stmt-query connection context issue (likely wrong default database), not a real table absence.

To reliably search for subtables of a specific model, use `information_schema.ins_tables` via stmt-query:

```json
{
  "count_stmt": "SELECT COUNT(*) FROM information_schema.ins_tables WHERE db_name = 'dedge' AND table_name LIKE '%<tm_code_lowercase>%'",
  "stmt": "SELECT table_name FROM information_schema.ins_tables WHERE db_name = 'dedge' AND table_name LIKE '%<tm_code_lowercase>%'",
  "args": {}
}
```

This works regardless of the stmt-query connection's default database context and returns 0 rows cleanly when no subtables exist for the model. Useful query patterns:
- Search by tm_code: `table_name LIKE '%<tm_code_lowercase>%'` (subtable names embed the tm_code)
- List subtables of a supertable: `stable_name = 'dedge_DOUBLE'` (ins_tables has a `stable_name` column)
- Count subtables per supertable: `SELECT COUNT(*) FROM information_schema.ins_tables WHERE db_name = 'dedge' AND stable_name = '<stable_name>'`

This is strictly a metadata query — no data scan, no timeout risk. Prefer it over `SHOW TABLES LIKE` or `DESCRIBE` for verifying whether a specific model has TDengine subtables.

## Pre-dashboard data existence verification

Before creating longstmts or dashboards for a tm_code the agent has not previously worked with, verify data existence in this order:

1. **Cloud model existence**: `dedge cloud tm ls --tm_code <code> --pageSize 1` — returns `total: 0` if the model doesn't exist in Cloud. This is faster and more direct than parsing `tm tree --json`. Do not proceed if the model doesn't exist.
2. **TDengine data probe**: `stmt-query` with `SELECT COUNT(*) FROM dedge_DOUBLE WHERE ts > '<recent_start>' AND ts < '<recent_end>' AND tm_code = '<code>'` (5-minute window, then widen if 0). Check all relevant supertables (DOUBLE/INT/BOOL).
3. **InfluxDB data probe** (if TDengine has no data): Flux `from(bucket: "dedge") |> range(...) |> filter(fn: (r) => r["tm_code"] == "<code>") |> limit(n: 1)` — returns `rowCount: 0` cleanly when no data exists.

If all three return empty, report to the user that the model has no data and ask for confirmation before proceeding. Do not create longstmts or dashboards for models with no data unless the user explicitly requests pre-provisioning (see "Zero-data stmt-query still registers a valid success sample" above).

## HSL gateway as data collection diagnostic

When TDengine/InfluxDB has no data for a model, the HSL edge gateway can confirm whether the device itself is alive and collecting. Use `dedge hsl read value <device_name>` to get real-time point values directly from the gateway, bypassing the entire Cloud→TSDB pipeline. This isolates the problem to either the device/gateway layer or the gateway→Cloud uplink layer.

### HSL login

The HSL component address is in Cloud's `tc ls` output (`tc_address` field), with credentials in `tc_cfg_content` JSON (`username`/`password`). Login with:

```bash
dedge hsl login <tc_address> <username> <password>
```

### Common HSL failure: MQTT uplink broken

If `dedge hsl device ls` or `dedge hsl read value <device>` returns empty with stderr like `802_ErrorNotRegistered: 读取CONNACK失败: EOF`, the HSL gateway's MQTT connection to Cloud is broken. The device and local collection may still work (`read value` succeeds), but no data flows to TSDB. This is a Cloud/infrastructure issue outside agent scope — report to user.

## Pitfalls

- **Flux on TDengine fails silently**: `stmt-query` with Flux syntax returns `code: 4, msg: "执行查询失败: [0x118] Invalid parameters"` on TDengine. This is not a real parameter error — it means TDengine does not support Flux.
- **`dedge ts-singleserver` is not a valid command prefix**: Use `dedge tss` for all TSS CLI commands. `dedge ts-singleserver` returns the top-level dedge help text. This skill previously documented `ts-singleserver` extensively — all those references have been corrected to `dedge tss`.
- **`gen-table-name` requires `--data` or `--file`, not individual flags**: The command does not accept `--tm_code`, `--data_type` etc. as CLI flags. Pass a JSON body via `--data '<json>'` or `--file <path>`. The body must contain a `tmagg` object with `tm_code`, `data_type` (not `td_data_type`), `tl_code`, and `prop` fields. Example: `{"tmagg": {"tm_code": "<code>", "data_type": "DOUBLE", "tl_code": "<tl_code>", "prop": "<prop>"}}`.
- **`longstmt ls` may include the template**: In current TSS versions, `longstmt ls --json` DOES return `stmt_template`, `stmt_hash16`, `uri_segment`, `tds_code`, `wrapper_name`, and `schema_json` (as a JSON string) for each entry. If the template field is present, you can inspect it directly from the list output without calling `longstmt get -id <id>`. If it's missing or null, fall back to `longstmt get -id <id>`.
- **KILL QUERY is not a reliable recovery mechanism**: TDengine 3.3.2.0 supports `SHOW CONNECTIONS` and `KILL QUERY <connection_id>` via `stmt-query`. However, TSS uses a connection pool — the agent cannot determine which connection_id was assigned to its own query. `SHOW CONNECTIONS` returns all active connections (TSS pool, Grafana Infinity, other clients) with no field to distinguish ownership. Therefore, prevention via query sizing (see "查询安全策略" section) is the only viable approach. Details in `references/data-inventory-procedure.md`.
- **`gen-table-name` data_type format**: The `data_type` field must be UPPERCASE and match TDengine type names, not Cloud `td_data_type` values. The mapping is: Cloud `DOUBLE`→`"DOUBLE"`, `INT`→`"INT"`, `BOOL`→`"BOOL"`, `LONG`→`"BIGINT"`. Passing `"LONG"` (the Cloud td_data_type) returns: `ParseDataFormatString规范化 dataType 失败: datatype不能解析`. Other invalid values like `"INT64"`, `"FLOAT"`, `"FLOAT64"` also fail. The `tl_code` field is also required for correct sub_table naming — without it, the prefix becomes `dunknown_` instead of `d<tl_code>_`.
- **Numeric schema keys**: TDengine schema_json uses `"1"`, `"2"` as property keys, not named keys like `"start"`, `"stop"`. This matches the `?` positional placeholder order in the SQL template.
- **JSON parsing with control chars, schema warnings, and truncated CLI output**: Cloud `--json` output frequently prepends non-JSON warning lines before the actual JSON, e.g. `警告: 服务端响应与 schema 不一致:\nvalidation failure list:\ndata.list.prop_type in body should be ...`. These warnings do not affect data integrity — `data.list` is still complete.
  - **Preferred parsing method (works for large outputs, 500+ props)**: Pipe the CLI output directly to a Python one-liner via stdin — this avoids terminal-tool truncation entirely and handles schema warnings by slicing from first `{` to last `}`:
    ```bash
    dedge cloud tm prop ls -tmCode <code> -page 1 -pageSize 1000 --json 2>/dev/null | python3 -c "
    import sys, json
    raw = sys.stdin.read()
    data = json.loads(raw[raw.index('{'):raw.rindex('}')+1], strict=False)
    props = data['data']['list']
    # process props...
    "
    ```
  - **Why NOT redirect to file + read_file**: The terminal tool caps stdout (50KB) and read_file truncates large files on line boundaries. For a 566-prop model (13K+ lines of JSON), the file read returns only a fragment, causing `json_parse()` to fail with `Expecting property name` — a structural incompleteness that `strict=False` cannot fix.
  - **Why NOT grep-only extraction on a saved file**: When the CLI output is saved to a file and then read back via the terminal tool, only a fragment (e.g. `tail -30`) may be captured, producing a subset of props. The stdin pipe method avoids this entirely.
  - **Fallback if stdin pipe is unavailable**: Use `grep -oP` field extraction directly on the raw CLI output piped from the command (not a saved file), then group in Python with `re.match(r'^([A-Z_]+)', code)` and `collections.Counter`.
- **Cloud prop listing CLI syntax**: The command is `dedge cloud tm prop ls -tmCode <code> -page 1 -pageSize 500`. The flag is `-tmCode` (camelCase, single-dash), NOT `--tm_code` (snake_case) — the latter returns "flag provided but not defined: -tm_code". This flag convention applies across **all** `dedge cloud tm` subcommands (Cloud commands use single-dash camelCase; TSS commands like `dedge ts-singleserver` use double-dash snake_case like `--tds_code`). When unsure, check `dedge cloud tm <subcommand> --help`.
  The response wraps props inside `{code, data: {list: [...], page, pageSize, total}, msg}` — props are in `data.list`, not at the top level. Each prop object has both `data_type` and `td_data_type` fields; group by `td_data_type` to map props to TDengine tables. **Pagination**: `total` may exceed `pageSize` (e.g. total=566 with pageSize=500). Always check `total` vs retrieved count and paginate if needed. Use `-pageSize 1000` to fetch everything in one call when the model has hundreds of props.
- **Cloud prop counts ≠ TDengine table counts**: Cloud `tm prop ls` (see syntax above) categorizes props by `data_type`, while TDengine tables are assigned by `td_data_type`. These can differ significantly. Always use `gen-table-name` per td_data_type to discover actual tables — never infer table membership from Cloud prop counts.
- **Bulk vs key prop grouping for dashboard planning**: Thing models with hundreds of props typically have a small set of "key" single props (e.g. VOL, SOC, SOH, TEMP_AVG) plus large numbered groups (e.g. CUR1~CUR51, ADD1~ADD300). Use a regex like `^(ADD|LIFT|FAULT_CODE|SOC_LOW_ACK|CUR)\d+$` to filter out bulk props when scoping a focused dashboard, then decide which bulk groups to include separately. This avoids presenting the user with an overwhelming flat list of 500+ prop codes. The recommended exploration pattern: pipe the prop listing through the stdin-pipe Python method (see the JSON parsing pitfall above) to get ALL props, then group by `re.match(r'^([A-Z_]+)', code)` and count per prefix with `collections.Counter` to produce a compact summary table (prefix, count, data_type, sample) that can be shown to the user for dashboard focus selection. Do NOT attempt the grouping on a file read via the terminal tool — it may only return a subset of props.
- **Catalog tree node type is 'directory', not 'folder'**: When writing `dashboard-catalog.json` tree nodes for Grafana folders, the `type` field must be `"directory"` — verified against the schema enum and frontend `CatalogTreeItem.vue`. Grafana's "folder" concept maps to catalog `directory` nodes, but the type strings are different vocabularies. Using `"folder"` silently breaks the frontend (node treated as leaf, children not rendered). Consult `dashboard-catalog.schema.json` for authoritative field constraints.
- **Do NOT create skills with `category` in this project**: `.hermes/.gitignore` uses `skills/*/` to ignore all skill directories, then reverse-includes specific ones via `!skills/<skill-name>/SKILL.md`. Creating a skill with `category: datacenter-agent` places it at `skills/datacenter-agent/<skill-name>/` — a nested path the reverse-include rules don't match, so it stays untracked. Create project skills WITHOUT a category (flat under `skills/`), then add `!skills/<name>/` + `!skills/<name>/SKILL.md` lines to `.gitignore`.
- **Backend `POST /api/current-view` overwrites catalog placeholders**: When the backend persists currentView via its API, it resolves `{agentmemory.*}` placeholders to real URLs and writes the resolved value back to `dashboard-catalog.json`, also resetting `currentView.updatedAt` to `null`. This silently violates the catalog placeholder invariant (all URLs must use `{agentmemory.*}` format). **Fix**: after calling `POST /api/current-view`, always re-patch the catalog file to restore placeholder format and set `updatedAt` to the correct timestamp. Verify with a grep that no hardcoded IPs leaked into the file. This is a backend behavior, not a Grafana or TSS issue — the backend's `_resolve_placeholders` in `service.py` resolves at API-read time but also persists the resolved form to disk.
- **Cloud tm_code existence check — use `tm ls`, not `tm tree`**: `dedge cloud tm ls --tm_code <code> --pageSize 1` returns `total: 0` immediately if the model doesn't exist. Parsing `tm tree --json` and searching is slower and more fragile. Use `tm tree` only when you need the full hierarchy (parent models, paths, etc.).

## Authority

1. Live `dedge ts-singleserver` command output and HTTP behavior.
2. `dedge-datacenter/.hermes/` bundled skills (datacenter-agent-cloud-tss-query for Flux/InfluxDB workflow, datacenter-agent-grafana-dashboard for Infinity panel configuration).
3. `dedge-datacenter/runtime/agent-memory/tsdb-memory.json` for data source addresses.
