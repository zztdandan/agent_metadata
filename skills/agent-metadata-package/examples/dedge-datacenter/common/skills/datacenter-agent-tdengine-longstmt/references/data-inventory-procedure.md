# Data Inventory Procedure — Reproduction Recipe

Condensed commands for determining which thing models have real data across all configured TSDB data sources.

## Prerequisites

Read `dedge-datacenter/runtime/agent-memory/tsdb-memory.json` for `tdsCode` values and credentials. All TSS commands use prefix `dedge ts-singleserver` (NOT `dedge tss`).

## Step 1: List all thing models

```bash
dedge cloud tm tree --json > /tmp/tm-tree.json
```

Extract all `tm_code` values recursively from `model_attributes` in the JSON. Typical yield: 50-70 models.

### Fast single-model existence check

To verify whether a specific tm_code exists in Cloud (e.g. user-provided name that may not match any model):

```bash
dedge cloud tm ls --tm_code <code> --pageSize 1
```

Returns `total: 0` if the model doesn't exist. This is faster and more reliable than parsing `tm tree --json` for a single lookup. Use `tm tree` only when the full hierarchy is needed.

### Pre-dashboard data existence verification

Before creating longstmts or dashboards for an unfamiliar tm_code, verify in this order:

1. **Cloud**: `dedge cloud tm ls --tm_code <code> --pageSize 1` — `total: 0` means the model doesn't exist.
2. **TDengine**: `stmt-query` with `SELECT COUNT(*) FROM dedge_DOUBLE WHERE ts > '<start>' AND ts < '<end>' AND tm_code = '<code>'` (5-min window). A `[0x2603] Table does not exist` error (code: 4) means no subtable exists for this model. Note: `gen-table-name` will STILL succeed (returns valid-looking names) even when no table exists — it's a naming convention generator, not an existence check.
3. **InfluxDB**: Flux `from(bucket: "dedge") |> range(...) |> filter(fn: (r) => r["tm_code"] == "<code>") |> limit(n: 1)` — `rowCount: 0` means no data.

If all three return empty, report to the user and ask for confirmation before proceeding.

## Step 2: Scan InfluxDB measurements

### 2a. List measurements with data (7-day window)

```bash
cat > /tmp/list-measurements-7d.json << 'EOF'
{
  "stmt": "from(bucket: params.bucket) |> range(start: time(v: params.start), stop: time(v: params.stop)) |> group(columns: [\"_measurement\"]) |> last() |> keep(columns: [\"_measurement\", \"_time\"]) |> filter(fn: (r) => not (r._measurement =~ /^(go_|boltdb_|qc_|storage_|task_|http_|query_|service_|influxdb_)/) )",
  "args": {
    "bucket": "dedge",
    "start": "2026-07-23T00:00:00Z",
    "stop": "2026-07-30T10:00:00Z"
  }
}
EOF

dedge ts-singleserver tsdb stmt-query --tds_code InfluxDB_network_server --file /tmp/list-measurements-7d.json
```

### 2b. Wider scan (180d) with internal-metric filter

```bash
cat > /tmp/list-measurements-wide.json << 'EOF'
{
  "stmt": "from(bucket: params.bucket) |> range(start: time(v: params.start), stop: time(v: params.stop)) |> group(columns: [\"_measurement\"]) |> last() |> keep(columns: [\"_measurement\", \"_time\"]) |> filter(fn: (r) => not (r._measurement =~ /^(go_|boltdb_|qc_|storage_|task_|http_|query_|service_|influxdb_)/) )",
  "args": {
    "bucket": "dedge",
    "start": "2026-01-01T00:00:00Z",
    "stop": "2026-07-30T10:00:00Z"
  }
}
EOF

dedge ts-singleserver tsdb stmt-query --tds_code InfluxDB_network_server --file /tmp/list-measurements-wide.json
```

### 2c. Discover tl_code tags per measurement

```bash
cat > /tmp/list-tlcodes.json << 'EOF'
{
  "stmt": "from(bucket: params.bucket) |> range(start: time(v: params.start), stop: time(v: params.stop)) |> group(columns: [\"tl_code\", \"_measurement\"]) |> last() |> keep(columns: [\"tl_code\", \"_measurement\", \"_time\"])",
  "args": {
    "bucket": "dedge",
    "start": "2026-01-01T00:00:00Z",
    "stop": "2026-07-30T10:00:00Z"
  }
}
EOF

dedge ts-singleserver tsdb stmt-query --tds_code InfluxDB_network_server --file /tmp/list-tlcodes.json
```

Note: Grouping by `tl_code` alone (without `_measurement`) causes "schema collision: cannot group float and boolean types together" — always group by both.

### 2d. InfluxDB-only pitfalls

- `import "influxdata/influxdb/schema"` → rejected: "stmt must be readonly query"
- `distinct(column: "_measurement")` over 7d range → timeout (context deadline exceeded)
- Without the internal-metric filter, all 124 results are InfluxDB self-monitoring (go_*, boltdb_*, storage_*, etc.)
- Direct InfluxDB API calls with the token from tsdb-memory.json may return 401 unauthorized (org mismatch or token scope)

## Step 3: Probe TDengine per model

For each model, get a valid prop first, then query with 1-minute window:

```bash
# Get first prop for a model
dedge cloud tm prop ls -tmCode <tm_code> -pageSize 5 -json

# Probe TDengine (1-minute window)
cat > /tmp/td-probe.json << 'EOF'
{
  "tmagg": {
    "tm_code": "<tm_code>",
    "prop": "<prop_code>",
    "data_type": "<DOUBLE|INT|BOOL|BIGINT>"
  },
  "start_time": "2026-07-10T02:24:00Z",
  "end_time": "2026-07-10T02:25:00Z"
}
EOF

dedge ts-singleserver tsdb query -tds_code TDengine_network_server -file /tmp/td-probe.json
```

### Interpreting TDengine probe results

| Response pattern | Meaning |
|---|---|
| `rowCount > 0` with `meta.tableName` present | Table exists, data in this time window |
| `rowCount = 0` with `meta.tableName` present | Table exists, no data in this time window |
| `rowCount = 0`, error `[0x2603] Table does not exist` | No TDengine table for this model |
| Error `[0x73a] Query memory exhausted` | Table has heavy data — narrow to 1-minute window |
| Error `[0x118] Invalid parameters` (from stmt-query) | stmt-query doesn't support TDengine SQL — use `query` command instead |

### Fast subtable existence check via information_schema

When you only need to verify whether a tm_code has any TDengine subtables (without probing for data), use `information_schema.ins_tables`:

```bash
cat > /tmp/check-subtables.json << 'EOF'
{
  "stmt": "SELECT table_name FROM information_schema.ins_tables WHERE db_name = 'dedge' AND table_name LIKE '%<tm_code_lowercase>%'",
  "args": {}
}
EOF

dedge ts-singleserver tsdb stmt-query --tds_code TDengine_network_server --file /tmp/check-subtables.json
```

Returns 0 rows when no subtables exist for the model. This is strictly metadata — no data scan, no timeout risk. Prefer this over `DESCRIBE` (which may fail due to stmt-query connection context issues) or `SHOW TABLES LIKE` (which requires the correct database context).

Note: `DESCRIBE dedge.dedge_DOUBLE` via stmt-query may return "Table does not exist" even when the supertable exists (confirmed by `SHOW STABLES`) and has subtables (confirmed by `information_schema.ins_tables`). This is a stmt-query connection context limitation, not a real table absence.

### TDengine query command notes

- `dedge ts-singleserver tsdb query` uses tmagg format (NOT Flux, NOT raw SQL)
- `dedge ts-singleserver tsdb stmt-query` with TDengine SQL returns `[0x118] Invalid parameters` — stmt-query wrapper is Flux-only. **Exception**: `stmt-query` DOES work for TDengine metadata commands like `SHOW TABLES`, `SHOW STABLES`, `DESCRIBE`, `SELECT SERVER_VERSION()`, and `SHOW CONNECTIONS`.
- TDengine REST API (port 6041) is typically not exposed outside the Docker network
- The `query` command schema: Body = `{tmagg: {tm_code, prop, data_type, [agg], [interval]}, start_time, end_time, [filters]}`
- Optional `agg` field: `"last"` for aggregation; `interval`: e.g. `"1h"`

## Step 4: Pinpoint data freshness

Binary search by progressively narrowing time windows. Use the TSS HTTP endpoint directly (not CLI) for speed:

```bash
# Phase 1: Hour-boundary scan (1 request per hour)
curl -s -m 15 -u "admin:<pass>" -H "Content-Type: application/json" \
  -d '{"args":{"1":"2026-07-30T01:00:00Z","2":"2026-07-30T02:00:00Z"}}' \
  http://<tss_url>/api/v1/query/<uri_segment>
# Check data.meta.rowCount — find the last hour with rowCount > 0

# Phase 2: Within that hour, scan 15-min blocks
# Phase 3: Within that 15-min block, scan 5-min blocks
# Phase 4: Within that 5-min block, scan 1-min blocks
# The last row's "last(ts)" field gives the exact final data point timestamp
```

Key signals:
- `rowCount > 0` with rows present → check `rows[-1]["last(ts)"]` for the exact last timestamp
- `rowCount = 0, columns = []` → no data in this window at all
- `rowCount = 0, columns = [...]` → table exists but window is empty (shouldn't happen if hour-boundary scan found data)

For high-frequency models (50ms sampling), expect ~600-625 rows per minute per prop type when data is flowing. When rowCount drops from ~22K/hour to ~8K/hour to 0 within consecutive hours, the data stopped mid-hour.

## Step 5: List Cloud thinglinks

```bash
dedge cloud tl ls -json
```

Returns all `tl_code` values. Cross-reference: models whose data carries a `tl_code` that appears in this list are actively linked. Note: the response may include a schema validation warning (non-JSON prefix) — extract JSON from first `{` to last `}`.

## Known data source state (as of 2026-08-04)

- **InfluxDB** (`InfluxDB_network_server`): 124 measurements, all internal monitoring except 7 device measurements from 2026-04-16 (stale 3.5+ months). Device measurements: `num9-shuichul-*`, `tmagg-influx-*`.
- **TDengine** (`TDengine_network_server`): Only `DADEVICE_COLL_1` has tables. Data flows at 50ms, ~620 rows/min. **Table naming migrated on ~2026-07-30**: data stopped flowing to old model-specific super tables (e.g. `dadevice-coll-1_double_4e7cde5f`, last data 2026-07-30T02:21:37Z) and resumed on new shared type-based super tables (`dedge_DOUBLE`, `dedge_INT`, `dedge_BOOL`). Migration confirmed 2026-08-04: new longstmts created querying `dedge_DOUBLE/INT/BOOL` with `tm_code = 'DADEVICE_COLL_1'` filter, all return live data. Old super tables still exist in `SHOW STABLES` but receive no new data. To query current data, use the shared super tables with `WHERE tm_code = '<tm_code>'` filter. Use `gen-table-name` (with `data_type` in UPPERCASE and `tl_code`) to discover the current `main_table` name.
- **Prometheus** (`PrometheusTSDB_network_server`): Connected but cannot enumerate metrics via stmt-query (PromQL not supported by the Flux/SQL wrapper).
- All three data sources share `thinglink_refs: ["hsl", "test0212"]` but only `test0212` has actual data flowing (to DADEVICE_COLL_1 in TDengine via `dedge_DOUBLE` shared super table).

## Query safety: TDengine KILL QUERY investigation

TDengine 3.3.2.0 supports `SHOW CONNECTIONS` and `KILL QUERY <connection_id>` via `stmt-query`. However, TSS uses a connection pool — the agent cannot determine which connection_id was assigned to its own query. `SHOW CONNECTIONS` returns all active connections (TSS pool, Grafana Infinity, other clients) with no field to distinguish which belongs to the agent's current query. Therefore, **KILL QUERY is not a reliable recovery mechanism** for the agent. Prevention via query sizing (see "查询安全策略" in SKILL.md) is the only viable approach.
