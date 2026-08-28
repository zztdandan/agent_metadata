# Virtual Device Model (VGATE_VIRTUAL_TM) Data Routing

Session: 2026-08-13, model `virtual_0416`

## Model characteristics

- `tm_code`: virtual_0416
- `tm_dri_code`: VGATE_VIRTUAL_TM
- `tm_coll_type`: VIRTUAL
- `tm_type_code`: VIRTUAL_DEVICE
- 4 INT props: virtual_182, virtual_195, virtual_119, virtual_205
- Each prop aliases to DADEVICE_COLL_1 model props via `add_cfg_frm_content`:
  - `{"alias_tm_code":"DADEVICE_COLL_1","alias_prop_code":"ADD182"}`
  - `{"alias_tm_code":"DADEVICE_COLL_1","alias_prop_code":"ADD195"}`
  - `{"alias_tm_code":"DADEVICE_COLL_1","alias_prop_code":"ADD119"}`
  - `{"alias_tm_code":"DADEVICE_COLL_1","alias_prop_code":"ADD205"}`

## Data source routing

- Data found in InfluxDB (not TDengine), bucket=20260601
- measurement=dedge_INT (shared type supertable)
- Data stored under tm_code=`virtual_0416` (NOT the aliased DADEVICE_COLL_1)
- tl_code tag=`test0212`
- Data time range: approximately 2026-08-12T00:00Z to 2026-08-12T08:24Z UTC
- Sampling rate: ~100ms per prop
- 2-hour COUNT: ~265K rows total (4 props × ~65K rows each)

## tmagg query vs Flux discrepancy

`dedge ts-singleserver tsdb query` (tmagg format) returned 0 rows / None for:
- 5min, 1h, 24h, 7d ranges with tm_code=virtual_0416
- 1h, 7d ranges with tm_code=DADEVICE_COLL_1 (aliased model)
- TDengine also returned 0 rows / memory exhausted for wide ranges

Flux `stmt-query` with same parameters successfully returned 40 rows (limit 10)
and 120 rows (5-min window, sorted desc, limit 5).

Conclusion: Flux stmt-query is more reliable than tmagg query for InfluxDB
exploratory probing. Always use Flux when tmagg returns 0 but data is expected.

## Longstmt created

- URI segment: e822c6ead8843fc1
- tds_code: InfluxDB_network_server
- Template: Flux with aggregateWindow(every: duration(v: params.interval), fn: mean)
- Parameters: bucket, start, stop, measurement, tm_code, interval
- Verified: 120 rows returned for 5-min window with 10s interval

## Grafana dashboard

- UID: be8f337c-a936-4eb9-bf91-91d5cf2f7a1b
- 5 panels: 1 timeseries (4 props) + 4 stat cards
- Public dashboard accessToken: d7a57f28daa0404b80c0c29b5cefe803
- Dashboard time range set to absolute: 2026-08-12T00:00:00Z to 2026-08-12T09:00:00Z
  (data stopped hours before session time; relative now-5m would show nothing)

## Key lessons

1. Virtual model data is stored under the virtual model's own tm_code, not the
   aliased model's tm_code.
2. When data is not live (stopped hours ago), dashboard time range must be set
   to absolute timestamps covering the data period, not relative now-Xm.
3. Flux aggregateWindow with parameterized interval is the correct approach for
   high-frequency virtual model data in InfluxDB.
4. gen-table-name returns `dunknown_` prefix when tl_code is not provided — this
   is expected for virtual models and does not affect data availability.
