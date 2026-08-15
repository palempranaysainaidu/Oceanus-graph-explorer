# Argo CSV → CognoDB graph mapping

## CSV summary (`backend-maps/argo_data.csv`)

| Column | Type / unit | Example | Graph use |
|--------|-------------|---------|-----------|
| `time` | ISO timestamp | `2019-01-01T11:00:58Z` | `Measurement.timestamp`, `Cruise.start_date` / `end_date` |
| `latitude` | degrees_north | `6.633` | `Float.lat` (mean per float) |
| `longitude` | degrees_east | `94.759` | `Float.lon` (mean per float) |
| `pres` | decibar (depth) | `4.7` | `Measurement.depth` |
| `temp` | °C | `29.232` | `Measurement.value` → Parameter `Temperature` |
| `temp_qc` | quality flag | `1` | optional QC (not in graph yet) |
| `psal` | PSU | `32.59` | `Measurement.value` → Parameter `Salinity` |
| `psal_qc` | quality flag | `1` | optional QC |
| `pres_qc` | quality flag | `1` | optional QC |
| `data_mode` | char | `A` | `Float.status` |
| `platform_number` | WMO id | `1901442` | `Float.id`, `Float.wmo_id` |
| `cycle_number` | int | `295` | `Cruise.id` = `{platform}_{cycle}` |
| `position_qc` | flag | `1` | optional |
| `direction` | char | `A` | optional |

**Scale:** ~462,174 rows · **88** distinct `platform_number` · ~77 cycles/float on average (1–213).

Row 2 is a units header (skipped on load: `skiprows=[1]`).

## Schema mapping (assignment)

```
CSV platform_number  →  Float.id, Float.wmo_id
CSV latitude/longitude (mean)  →  Float.lat, Float.lon
CSV data_mode  →  Float.status

CSV cycle_number  →  Cruise.id = "{platform}_{cycle}", Cruise.name = "Cycle N"
CSV time (min/max per cycle)  →  Cruise.start_date, Cruise.end_date

lat/lon rules  →  Region.name (Arabian Sea, Bay of Bengal, …)

CSV temp/psal/pres  →  Measurement.value + MEASURES → Parameter
CSV pres  →  Measurement.depth
CSV time  →  Measurement.timestamp

Float centroids (≤120 km)  →  (:Float)-[:NEAR {distance_km}]->(:Float)
```

## Seed script

```bash
cd backend-chatbot-test
python Data_populating/seed_graph.py          # profile-level measurements (~20k)
python Data_populating/seed_graph.py --clear  # wipe first
python Data_populating/seed_graph.py --full-depth  # all depth rows (~1.4M nodes, slow)
```

## Example queries (your schema)

**Multi-hop (region + parameter):**
```cypher
MATCH (f:Float)-[:LOCATED_IN]->(:Region {name: $region})
MATCH (f)-[:RECORDED]->(m:Measurement)-[:MEASURES]->(p:Parameter {name: $param})
RETURN f.id, avg(m.value) AS avg_value
ORDER BY avg_value DESC
```

**Proximity network:**
```cypher
MATCH (f1:Float)-[:NEAR*1..3]-(f2:Float)
WHERE f1.id = $floatId
RETURN DISTINCT f2.id, f2.lat, f2.lon
```
