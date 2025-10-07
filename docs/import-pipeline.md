# Import Pipeline

## Flow
1. **File ingestion**
   - `import-service` watches `IMPORT_WATCH_PATH` or receives uploads.
   - Files (`.csv`, `.xlsx`, `.xlsm`) are parsed into a structured payload (trebovanje header + line items).
2. **Catalog enrichment**
   - For every `stavka`, import-service calls `GET {TASK_SERVICE_INTERNAL_URL}/internal/catalog/lookup?sifra=…` with `Authorization: Bearer <SERVICE_TOKEN>`.
   - If the item exists, the payload is enriched with `artikl_id` and missing `barkod` (primary barcode if available).
   - If no barcode is available after enrichment, `needs_barcode=true` is set on the line. This drives the audit metrics and downstream UI badges.
3. **Task-service import**
   - Enriched payload is posted to `POST {TASK_SERVICE_URL}/api/trebovanja/import` with service user headers.
   - Task-service stores the trebovanje, assigns `needs_barcode` flags, and records two audit events:
     - `trebovanje.imported` – document metadata.
     - `catalog.enriched` – counts of `enriched` vs `needs_barcode` line items.

## Payload snippet
```json
{
  "dokument_broj": "DOC-42",
  "datum": "2025-05-01T08:00:00Z",
  "magacin_pantheon_id": "veleprodajni_magacin",
  "radnja_pantheon_id": "prodavnica_kotor_centar",
  "stavke": [
    {
      "artikl_sifra": "200431",
      "naziv": "Jastuk KING",
      "kolicina_trazena": 5,
      "barkod": "8600100200431",
      "artikl_id": "<uuid>",
      "needs_barcode": false
    },
    {
      "artikl_sifra": "200555",
      "naziv": "Navlaka",
      "kolicina_trazena": 3,
      "needs_barcode": true
    }
  ]
}
```

## Configuration
| Variable | Service | Description |
| --- | --- | --- |
| `IMPORT_WATCH_PATH`, `IMPORT_PROCESSED_PATH`, `IMPORT_FAILED_PATH` | import-service | File system paths for incoming/processed/failed imports. |
| `TASK_SERVICE_URL` | import-service | Public API base (default `http://task-service:8001/api`). |
| `TASK_SERVICE_INTERNAL_URL` | import-service | Internal API base for catalog lookups (default `http://task-service:8000`). |
| `TASK_SERVICE_TIMEOUT_SECONDS` | import-service | HTTP timeout for both import and lookup calls. |
| `SERVICE_TOKEN` | import-service | Shared bearer token for `/internal/*` endpoints. |
| `SERVICE_USER_ID` | import-service | User context forwarded to task-service when creating trebovanja. |

## Error handling
- Parser errors (invalid quantity, missing columns) raise `ValueError` and the file is moved to `IMPORT_FAILED_PATH`.
- Lookup or import HTTP errors emit `import.process.failed` logs and the file is also moved to the failed folder.
- Duplicate documents reported by task-service are treated as success: file moves to processed, log `import.process.duplicate`.

## Metrics & Audits
- Task-service audit `catalog.enriched` captures line counts for each trebovanje.
- UI can surface the flag by checking `needs_barcode` per line; future PWA work can highlight missing barcodes using this flag.
