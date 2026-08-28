# InfluxDB Data Source Discovery (ModbusSim Session, 2026-08-12)

## Problem

ModbusSim model (tm_code=ModbusSim, tl_code=hsl) had 0 rows in TDengine across all time ranges (5min, 1h, 24h, 7d). The device was alive via HSL gateway (`dedge hsl read value ModbusSim` returned 200 prop values). Existing TDengine longstmts (uri: ca2779f76b3a291f, dfc6bfcac3c56032, cc834615963c4a33) all returned `rowCount: 0`.

## Root Cause

Data was being written to **InfluxDB**, not TDengine. The ts-singleserver was subscribed to MQTT topic `thingmodel/hsl/ModbusSim` and writing to InfluxDB bucket `20260601` — but `tsdb-memory.json` recorded the bucket as `dedge` with an expired token, causing all InfluxDB queries to silently return empty results.

## Diagnostic Procedure

### Step 1: Verify TDengine has no data

```bash
# COUNT with time range + tm_code filter (5min window)
cat > /tmp/count.json << 'EOF'
{"stmt": "SELECT COUNT(*) FROM `dedge_DOUBLE` WHERE ts > '2026-08-12T07:33:00Z' AND ts < '2026-08-12T07:38:00Z' AND tm_code = 'ModbusSim'", "args": {}}
EOF
dedge ts-singleserver tsdb stmt-query -tds_code TDengine_network_server -file /tmp/count.json --json
# Result: count=0
```

Widen to 7 days — still 0. Check `SHOW STABLES` — `dedge_BIGINT` doesn't exist at all. Check `SHOW TABLES LIKE 'dunknown_modbussim%'` — no subtables.

### Step 2: Verify device is alive via HSL

```bash
dedge hsl read value ModbusSim
# Returns 200 prop values (BOOL, INT, BIGINT, DOUBLE)
```

### Step 3: Check HSL MQTT publishing config

```bash
dedge hsl server-settings upload
# Key fields: UseMqttServer=true, MqttIpAddress=172.16.8.149, MqttPort=1883, UploadTimeInterval=1000
```

### Step 4: Verify MQTT data is flowing

Minimal Python MQTT subscriber (no paho-mqtt dependency):

```python
import socket, struct, time
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect(("172.16.8.149", 1883))
# CONNECT packet
client_id = b"agent-check-" + str(int(time.time())).encode()
payload = struct.pack("!H", 4) + b"MQTT" + struct.pack("!BBH", 4, 0, 60) + struct.pack("!H", len(client_id)) + client_id
sock.send(bytes([0x10]) + bytes([len(payload)]) + payload)
sock.recv(4)  # CONNACK
# SUBSCRIBE to thingmodel/hsl/#
topic = b"thingmodel/hsl/#"
payload = struct.pack("!H", 1) + struct.pack("!H", len(topic)) + topic + bytes([0])
sock.send(bytes([0x82]) + bytes([len(payload)]) + payload)
sock.recv(5)  # SUBACK
# Read messages
sock.settimeout(5)
data = sock.recv(8192)
# data contains: thingmodel/hsl/ModbusSim {"version":"mqttjsonv2","ts":...,"tags":{"tm_code":"ModbusSim","tl_code":"hsl"},"data":[...]}
```

### Step 5: Discover actual InfluxDB credentials from TSS config

```bash
curl -s -u "admin:<tss_password>" "http://<tss_host>:<tss_port>/api/v1/config/tsdb" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for ds in data.get('data', []):
    if ds.get('tds_type') == 'influxdb-v2':
        content = json.loads(ds.get('tds_content', '{}'))
        print(f'bucket={content[\"bucket\"]}, token={content[\"token\"][:30]}...')
"
# Result: bucket=20260601, token=ZhIAl3AwEKQ8UOZCXZ_ssHRP8g16Q_...
# tsdb-memory.json had: bucket=dedge, token=19cqeMwnp5TLVmoRaHRBbDhpXxL63pq_... (STALE!)
```

### Step 6: Query InfluxDB with correct bucket

```bash
cat > /tmp/flux.json << 'EOF'
{"stmt": "from(bucket: \"20260601\") |> range(start: time(v: \"2026-08-12T07:45:00Z\"), stop: time(v: \"2026-08-12T07:50:00Z\")) |> filter(fn: (r) => r.tm_code == \"ModbusSim\") |> group(columns: [\"_measurement\"]) |> count() |> limit(n: 10)", "args": {}}
EOF
dedge ts-singleserver tsdb stmt-query -tds_code InfluxDB_network_server -file /tmp/flux.json --json
# Result: dedge_BOOL: 14150 rows, dedge_DOUBLE: 42450 rows
```

### Step 7: Discover actual prop names in InfluxDB

Cloud prop_code `HR300_LONG_0` did NOT exist in InfluxDB. Actual BIGINT props started at `HR350_LONG_0`.

```bash
cat > /tmp/flux_props.json << 'EOF'
{"stmt": "from(bucket: \"20260601\") |> range(start: time(v: \"2026-08-12T07:45:00Z\"), stop: time(v: \"2026-08-12T07:50:00Z\")) |> filter(fn: (r) => r.tm_code == \"ModbusSim\") |> group(columns: [\"prop\"]) |> distinct(column: \"prop\") |> limit(n: 300)", "args": {}}
EOF
dedge ts-singleserver tsdb stmt-query -tds_code InfluxDB_network_server -file /tmp/flux_props.json --json
```

### Step 8: Create InfluxDB longstmt

Single longstmt with `measurement` parameter serves both DOUBLE and BOOL:

```
from(bucket: params.bucket) |> range(start: time(v: params.start), stop: time(v: params.stop)) |> filter(fn: (r) => r["_measurement"] == params.measurement) |> filter(fn: (r) => r["tm_code"] == params.tm_code) |> filter(fn: (r) => r["_field"] == "val") |> sort(columns: ["_time"]) |> limit(n: 500000)
```

Schema: `required: [bucket, start, stop, measurement, tm_code]`

Grafana panels pass `measurement: "dedge_DOUBLE"` or `measurement: "dedge_BOOL"` in `url_options.data.args`.

## HSL Type Flattening

The HSL gateway wrote all numeric types (INT, BIGINT, DOUBLE) as `data_type: "DOUBLE"` into `dedge_DOUBLE` measurement. Only BOOL went to `dedge_BOOL`. This means:

- 50 INT props + 50 BIGINT props + 50 DOUBLE props = 150 props in dedge_DOUBLE
- 50 BOOL props in dedge_BOOL
- No dedge_INT or dedge_BIGINT measurements exist in InfluxDB
- `dedge_BIGINT` supertable does not exist in TDengine

## InfluxDB TypeFrame Column Mapping for Grafana Infinity

InfluxDB longstmt returns columns: `table_name`, `timestamp`, `_field`, `_measurement`, `_time`, `_value`, `data_type`, `prop`, `result`, `table`, `tl_code`, `tm_code`, `topic`

For Grafana Infinity columns, use:
```json
"columns": [
    {"selector": "_time", "text": "Time", "type": "timestamp"},
    {"selector": "_value", "text": "Value", "type": "number"},
    {"selector": "prop", "text": "Prop", "type": "string"}
]
```

Note: InfluxDB TypeFrame uses `_time`/`_value`/`prop` (same as Flux native), while TDengine TypeFrame uses `last(ts)`/`last(val)`/`prop`. The Infinity column selectors must match the actual data source's column names.
