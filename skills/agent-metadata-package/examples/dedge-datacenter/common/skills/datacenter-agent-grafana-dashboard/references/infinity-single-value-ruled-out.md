# Infinity single-value stat panel: ruled-out approaches (2026-07-10)

All tested against Grafana 11.6.5 with `yesoreyeram-infinity-datasource`.

## 1. filterByValue(equal) → reduce

```json
"transformations": [
  {"id": "filterByValue", "options": {
    "filters": [{"fieldName": "Prop", "config": {"id": "equal", "options": {"value": "VOL"}}}],
    "type": "include", "match": "any"
  }},
  {"id": "reduce", "options": {"reducers": ["lastNotNull"]}}
]
```

**Result**: "No data" — the `equal` config variant fails silently in current Infinity plugin. The filter doesn't match even when the field value exactly equals the target.

**Fix**: Use `"id": "regex"` with `"options": {"value": "^VOL$"}` instead.

## 2. filterByValue(regex) → reduce (no organize)

```json
"transformations": [
  {"id": "filterByValue", "options": {
    "filters": [{"fieldName": "Prop", "config": {"id": "regex", "options": {"value": "^VOL$"}}}],
    "type": "include", "match": "any"
  }},
  {"id": "reduce", "options": {"reducers": ["lastNotNull"]}}
]
```

**Result**: "No data" — after filtering, the frame has three columns (Time, Value, Prop). `reduce` sees multiple fields and cannot determine which to reduce.

**Fix**: Insert `organize` with `excludeByName: {"Time": true, "Prop": true}` between filterByValue and reduce.

## 3. format: timeseries single prop (works but defeats caching)

Using per-prop longstmt with `format: timeseries` in a stat panel:

```json
"format": "timeseries",
"columns": [
  {"selector": "_time", "type": "timestamp"},
  {"selector": "_value", "text": "VOL", "type": "number"}
],
"url": "/api/v1/query/<perPropLongstmtUri>",
"url_options": {"data": "{\"args\":{...,\"prop\":\"VOL\"}}"}
```

**Result**: Works, but each stat panel makes a separate API call instead of sharing the cached full-model response. Defeats the multi-panel shared-query optimization.

## Working single-value stat panel approach (2026-07-10)

`format: table` + three-stage Grafana transform chain: `filterByValue(regex) → organize → reduce(lastNotNull)`

```json
"targets": [{
  "format": "table",
  "columns": [
    {"selector": "_time", "text": "Time", "type": "timestamp"},
    {"selector": "_value", "text": "Value", "type": "number"},
    {"selector": "prop", "text": "Prop", "type": "string"}
  ],
  "url": "/api/v1/query/<fullModelUri>",
  "url_options": {"data": "<identical body as other panels>"}
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

**Key insights**:
1. `organize` step is mandatory — hides non-numeric columns so `reduce` finds a single numeric field.
2. Always use regex mode in filterByValue, even for exact match — `"^PROP$"` avoids equal-mode bug.
3. Same target as multi-series panels — one API call serves the entire dashboard.
