# Infinity multi-series: ruled-out approaches (2026-07-10)

All tested against Grafana 11.6.5 with `yesoreyeram-infinity-datasource`.

## 1. Single target + string column for series discrimination (timeseries format)

```json
"format": "timeseries",
"columns": [
  {"selector": "_time", "type": "timestamp"},
  {"selector": "_value", "type": "number"},
  {"selector": "prop", "type": "string"}
]
```

**Result**: Creates ONE series named after the refId (e.g. "A"). String column ignored. Data aggregates into a single line.

## 2. per-target `filters` array (timeseries format)

```json
"format": "timeseries",
"filters": [{"field": "prop", "operator": "=", "value": "CUR1"}]
```

**Result without string column**: "No data" — filters silently produce nothing.
**Result with string column**: JS crash `(e.value || []).map is not a function` — Infinity internal error.

## 3. filterByName / filterFieldsByName transform

```json
"transformations": [{"id": "filterFieldsByName", "options": {"include": {"pattern": "^CUR[0-9]+$"}}}]
```

**Result**: `filterByName` → "not found" (wrong ID). `filterFieldsByName` → silent "No data" — field name patterns from Infinity don't match expected names.

## 4. format: series

```json
"format": "series"
```

**Result**: Same as timeseries — single series, no auto-split by string column.

## Working single-target approach (2026-07-10 — discovered)

`format: table` + three-stage Grafana transform chain: `filterByValue → partitionByValues → prepareTimeSeries`

```json
"targets": [{
  "format": "table",
  "columns": [
    {"selector": "_time", "text": "Time", "type": "timestamp"},
    {"selector": "_value", "text": "Value", "type": "number"},
    {"selector": "prop", "text": "Prop", "type": "string"}
  ],
  "url": "/api/v1/query/<fullModelUri>",
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

**Key insight**: `prepareTimeSeries` alone fails — it needs `partitionByValues` first to split the single table frame into per-prop frames. Omitting `partitionByValues` produces `"Data is missing a number field"`.

**Why this matters**: one API call instead of N. TSS caches the full-model response. Changing the prop set means editing a regex, not adding/removing targets.

## Fallback multi-target approach (still valid)

N targets, each with different `args.prop` value in `url_options.data`, pointing to a per-prop longstmt. Each target's value column `text` becomes the series name (e.g. "CUR1"). Use this if the transform chain misbehaves (e.g. Grafana version incompatibility).
