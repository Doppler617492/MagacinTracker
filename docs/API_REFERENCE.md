# API Reference - Shortage Tracking Endpoints

## Base URL

```
Production: https://api.magacin.com
Development: http://localhost:8123/api
```

## Authentication

All endpoints require JWT Bearer token (except login).

```http
Authorization: Bearer <access_token>
```

**Get Token:**
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Catalog Endpoints

### Lookup by Code

Lookup article by SKU or barcode.

```http
GET /api/catalog/lookup?code={code}
```

**Parameters:**
- `code` (string, required): SKU (sifra) or barcode

**Response: 200 OK**
```json
{
  "artikal_id": "550e8400-e29b-41d4-a716-446655440000",
  "sifra": "12345",
  "naziv": "Test Artikal",
  "jedinica_mjere": "kom",
  "aktivan": true,
  "barkodovi": [
    {
      "value": "1234567890123",
      "is_primary": true
    }
  ]
}
```

**Response: 200 OK (Not Found)**
```json
{
  "artikal_id": null,
  "sifra": "99999",
  "naziv": null,
  "jedinica_mjere": null,
  "aktivan": false,
  "barkodovi": []
}
```

**Errors:**
- `401 Unauthorized` - Invalid/missing token
- `400 Bad Request` - Missing code parameter

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/catalog/lookup?code=12345"
```

---

## Worker Picking Endpoints

### Pick by Code

Record a pick using scanned barcode or manually entered SKU.

```http
POST /api/worker/tasks/{stavka_id}/pick-by-code
Content-Type: application/json
```

**Path Parameters:**
- `stavka_id` (UUID, required): Trebovanje stavka ID

**Request Body:**
```json
{
  "code": "12345",
  "quantity": 5,
  "operation_id": "pick-abc123-1633024800"
}
```

**Fields:**
- `code` (string, required): Barcode or SKU scanned/entered
- `quantity` (float, required): Quantity picked (must be > 0)
- `operation_id` (string, required): Idempotency key

**Response: 200 OK**
```json
{
  "stavka_id": "550e8400-e29b-41d4-a716-446655440000",
  "picked_qty": 5,
  "required_qty": 10,
  "missing_qty": 5,
  "discrepancy_status": "none",
  "needs_barcode": false,
  "matched_code": "12345",
  "message": "Picked 5. Total: 5/10"
}
```

**Errors:**
- `400 Bad Request` - Validation errors:
  - "Code not found in catalog"
  - "Scanned item does not match expected item"
  - "Quantity exceeds remaining"
- `401 Unauthorized` - Invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Stavka ID not found

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"12345","quantity":5,"operation_id":"test-001"}' \
  "http://localhost:8123/api/worker/tasks/550e8400-e29b-41d4-a716-446655440000/pick-by-code"
```

---

### Record Short Pick

Record partial quantity (less than requested).

```http
POST /api/worker/tasks/{stavka_id}/short-pick
Content-Type: application/json
```

**Request Body:**
```json
{
  "actual_qty": 3,
  "reason": "Oštećeno",
  "operation_id": "short-abc123-1633024800"
}
```

**Fields:**
- `actual_qty` (float, required): Actual quantity picked (≥ 0)
- `reason` (string, optional): Reason for shortage
- `operation_id` (string, required): Idempotency key

**Response: 200 OK**
```json
{
  "stavka_id": "550e8400-e29b-41d4-a716-446655440000",
  "picked_qty": 3,
  "required_qty": 10,
  "missing_qty": 7,
  "discrepancy_status": "short_pick",
  "message": "Short pick recorded: 3/10"
}
```

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"actual_qty":3,"reason":"Oštećeno","operation_id":"short-001"}' \
  "http://localhost:8123/api/worker/tasks/550e8400-e29b-41d4-a716-446655440000/short-pick"
```

---

### Mark Not Found

Mark item as completely not found (picked_qty = 0).

```http
POST /api/worker/tasks/{stavka_id}/not-found
Content-Type: application/json
```

**Request Body:**
```json
{
  "reason": "Nema na lokaciji",
  "operation_id": "notfound-abc123-1633024800"
}
```

**Fields:**
- `reason` (string, optional): Why item wasn't found
- `operation_id` (string, required): Idempotency key

**Response: 200 OK**
```json
{
  "stavka_id": "550e8400-e29b-41d4-a716-446655440000",
  "picked_qty": 0,
  "required_qty": 10,
  "discrepancy_status": "not_found",
  "message": "Item marked as not found"
}
```

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason":"Nema na lokaciji","operation_id":"notfound-001"}' \
  "http://localhost:8123/api/worker/tasks/550e8400-e29b-41d4-a716-446655440000/not-found"
```

---

### Complete Document

Complete a trebovanje document, optionally with shortages.

```http
POST /api/worker/documents/{trebovanje_id}/complete
Content-Type: application/json
```

**Path Parameters:**
- `trebovanje_id` (UUID, required): Trebovanje document ID

**Request Body:**
```json
{
  "confirm_incomplete": true,
  "operation_id": "complete-abc123-1633024800"
}
```

**Fields:**
- `confirm_incomplete` (boolean, required): Must be `true` if shortages exist
- `operation_id` (string, required): Idempotency key

**Response: 200 OK**
```json
{
  "trebovanje_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_items": 15,
  "completed_items": 15,
  "items_with_shortages": 3,
  "total_shortage_qty": 12.5,
  "status": "done",
  "message": "Document completed with 3 shortage(s)"
}
```

**Errors:**
- `400 Bad Request`:
  - "Document has N items with shortages. Set confirm_incomplete=true to complete anyway."
  - "Trebovanje not found"
- `401 Unauthorized`
- `403 Forbidden`

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"confirm_incomplete":true,"operation_id":"complete-001"}' \
  "http://localhost:8123/api/worker/documents/550e8400-e29b-41d4-a716-446655440000/complete"
```

---

## Admin Report Endpoints

### Get Shortage Report

Retrieve shortage data with optional filters. Supports JSON and CSV output.

```http
GET /api/reports/shortages?from_date={date}&to_date={date}&format={format}
```

**Query Parameters:**
- `from_date` (string, optional): Start date (YYYY-MM-DD)
- `to_date` (string, optional): End date (YYYY-MM-DD)
- `radnja_id` (UUID, optional): Filter by store
- `magacioner_id` (UUID, optional): Filter by worker
- `discrepancy_status` (string, optional): Filter by status
  - Values: `short_pick`, `not_found`, `damaged`, `wrong_barcode`
- `format` (string, optional): Output format
  - Values: `json` (default), `csv`

**Response: 200 OK (JSON)**
```json
[
  {
    "trebovanje_dokument_broj": "25-20AT-000336",
    "trebovanje_datum": "2024-10-10 15:30",
    "radnja_naziv": "Radnja Budva",
    "magacin_naziv": "Transit Warehouse",
    "artikal_sifra": "12345",
    "artikal_naziv": "Test Artikal",
    "required_qty": 10,
    "picked_qty": 7,
    "missing_qty": 3,
    "discrepancy_status": "short_pick",
    "discrepancy_reason": "Oštećeno",
    "magacioner_name": "Gezim Maku",
    "completed_at": "2024-10-10 16:45"
  }
]
```

**Response: 200 OK (CSV)**
```csv
"Document","Date","Store","Warehouse","SKU","Article Name","Required Qty","Picked Qty","Missing Qty","Status","Reason","Worker","Completed At"
"25-20AT-000336","2024-10-10 15:30","Radnja Budva","Transit Warehouse","12345","Test Artikal","10","7","3","short_pick","Oštećeno","Gezim Maku","2024-10-10 16:45"
```

**Errors:**
- `401 Unauthorized`
- `403 Forbidden` - Only menadžer/šef/admin can access
- `400 Bad Request` - Invalid parameters

**Examples:**

JSON Report:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/reports/shortages?from_date=2024-10-01&to_date=2024-10-31&format=json"
```

CSV Export:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/reports/shortages?from_date=2024-10-01&format=csv" \
  -o shortage_report.csv
```

Filtered by Status:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/reports/shortages?discrepancy_status=not_found"
```

---

## Webhook Events (Future)

### Shortage Webhook

When a document is completed with shortages:

```http
POST https://your-webhook-url.com/shortages
Content-Type: application/json

{
  "event": "document.completed.with_shortages",
  "timestamp": "2024-10-10T14:30:00Z",
  "data": {
    "trebovanje_id": "uuid",
    "dokument_broj": "25-20AT-000336",
    "items_with_shortages": 3,
    "total_shortage_qty": 12.5,
    "worker": {
      "id": "uuid",
      "name": "Gezim Maku"
    },
    "shortages": [
      {
        "artikal_sifra": "12345",
        "naziv": "Test Artikal",
        "missing_qty": 3,
        "discrepancy_status": "short_pick",
        "reason": "Oštećeno"
      }
    ]
  }
}
```

---

## Rate Limits

| Endpoint Pattern | Limit | Window |
|-----------------|-------|--------|
| `/auth/login` | 5 requests | 1 minute |
| `/catalog/lookup` | 100 requests | 1 minute |
| `/worker/tasks/*/pick-by-code` | 60 requests | 1 minute |
| `/worker/tasks/*/short-pick` | 60 requests | 1 minute |
| `/worker/documents/*/complete` | 10 requests | 1 minute |
| `/reports/shortages` (JSON) | 10 requests | 1 minute |
| `/reports/shortages` (CSV) | 2 requests | 1 minute |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1633025400
```

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2024-10-10T14:30:00Z",
  "path": "/api/worker/tasks/123/pick-by-code"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `CODE_NOT_FOUND` | 400 | SKU/barcode not in catalog |
| `CODE_MISMATCH` | 400 | Scanned wrong item |
| `SHORTAGE_CONFIRMATION_REQUIRED` | 400 | Must set confirm_incomplete=true |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Idempotency

All write endpoints support idempotency via `operation_id`.

**Rules:**
1. `operation_id` must be unique per operation
2. Format: `{action}-{resource_id}-{timestamp}`
3. Server caches responses for 24 hours
4. Duplicate requests return cached response (no side effects)

**Example:**
```bash
# First request
POST /worker/tasks/123/pick-by-code
{"code":"12345","quantity":5,"operation_id":"pick-123-1633024800"}
→ 200 OK, pick recorded

# Duplicate request (same operation_id)
POST /worker/tasks/123/pick-by-code
{"code":"12345","quantity":5,"operation_id":"pick-123-1633024800"}
→ 200 OK, no change (cached response)
```

---

## Pagination

For list endpoints (future):

**Request:**
```http
GET /api/reports/shortages?page=1&per_page=50
```

**Response:**
```json
{
  "items": [...],
  "total": 250,
  "page": 1,
  "per_page": 50,
  "pages": 5
}
```

**Headers:**
```http
Link: <...?page=2>; rel="next", <...?page=5>; rel="last"
X-Total-Count: 250
```

---

## Versioning

Current API version: **v1**

**Version Header:**
```http
X-API-Version: 1.0
```

Future versions will use path-based versioning:
```
/api/v2/worker/tasks/{id}/pick-by-code
```

---

## OpenAPI Schema

**Swagger UI:**
```
http://localhost:8123/docs
```

**OpenAPI JSON:**
```
http://localhost:8123/openapi.json
```

**ReDoc:**
```
http://localhost:8123/redoc
```

---

## SDK Examples

### Python

```python
import httpx

class MagacinClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def lookup_code(self, code: str):
        response = httpx.get(
            f"{self.base_url}/catalog/lookup",
            params={"code": code},
            headers=self.headers
        )
        return response.json()
    
    def pick_by_code(self, stavka_id: str, code: str, quantity: float):
        response = httpx.post(
            f"{self.base_url}/worker/tasks/{stavka_id}/pick-by-code",
            json={
                "code": code,
                "quantity": quantity,
                "operation_id": f"pick-{stavka_id}-{int(time.time())}"
            },
            headers=self.headers
        )
        return response.json()
    
    def get_shortage_report(self, from_date: str, to_date: str):
        response = httpx.get(
            f"{self.base_url}/reports/shortages",
            params={
                "from_date": from_date,
                "to_date": to_date,
                "format": "json"
            },
            headers=self.headers
        )
        return response.json()

# Usage
client = MagacinClient("http://localhost:8123/api", token)
article = client.lookup_code("12345")
result = client.pick_by_code(stavka_id, "12345", 5)
```

### JavaScript/TypeScript

```typescript
import axios from 'axios';

class MagacinClient {
  private baseURL: string;
  private token: string;

  constructor(baseURL: string, token: string) {
    this.baseURL = baseURL;
    this.token = token;
  }

  async lookupCode(code: string) {
    const { data } = await axios.get(`${this.baseURL}/catalog/lookup`, {
      params: { code },
      headers: { Authorization: `Bearer ${this.token}` }
    });
    return data;
  }

  async pickByCode(stavkaId: string, code: string, quantity: number) {
    const { data } = await axios.post(
      `${this.baseURL}/worker/tasks/${stavkaId}/pick-by-code`,
      {
        code,
        quantity,
        operation_id: `pick-${stavkaId}-${Date.now()}`
      },
      { headers: { Authorization: `Bearer ${this.token}` } }
    );
    return data;
  }

  async getShortageReport(fromDate: string, toDate: string) {
    const { data } = await axios.get(`${this.baseURL}/reports/shortages`, {
      params: { from_date: fromDate, to_date: toDate, format: 'json' },
      headers: { Authorization: `Bearer ${this.token}` }
    });
    return data;
  }
}

// Usage
const client = new MagacinClient('http://localhost:8123/api', token);
const article = await client.lookupCode('12345');
const result = await client.pickByCode(stavkaId, '12345', 5);
```

---

## Postman Collection

Import this collection for easy API testing:

```json
{
  "info": {
    "name": "Magacin Track - Shortage API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [{"key": "token", "value": "{{access_token}}"}]
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/auth/login",
            "body": {
              "mode": "raw",
              "raw": "{\"username\":\"gezim.maku@cungu.com\",\"password\":\"Worker123!\"}"
            }
          }
        }
      ]
    },
    {
      "name": "Catalog",
      "item": [
        {
          "name": "Lookup by Code",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/catalog/lookup?code=12345"
          }
        }
      ]
    },
    {
      "name": "Picking",
      "item": [
        {
          "name": "Pick by Code",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/worker/tasks/{{stavka_id}}/pick-by-code",
            "body": {
              "mode": "raw",
              "raw": "{\"code\":\"12345\",\"quantity\":5,\"operation_id\":\"test-001\"}"
            }
          }
        },
        {
          "name": "Short Pick",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/worker/tasks/{{stavka_id}}/short-pick",
            "body": {
              "mode": "raw",
              "raw": "{\"actual_qty\":3,\"reason\":\"Oštećeno\",\"operation_id\":\"test-002\"}"
            }
          }
        },
        {
          "name": "Not Found",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/worker/tasks/{{stavka_id}}/not-found",
            "body": {
              "mode": "raw",
              "raw": "{\"reason\":\"Nema na lokaciji\",\"operation_id\":\"test-003\"}"
            }
          }
        },
        {
          "name": "Complete Document",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/worker/documents/{{trebovanje_id}}/complete",
            "body": {
              "mode": "raw",
              "raw": "{\"confirm_incomplete\":true,\"operation_id\":\"test-004\"}"
            }
          }
        }
      ]
    },
    {
      "name": "Reports",
      "item": [
        {
          "name": "Shortage Report (JSON)",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/reports/shortages?format=json"
          }
        },
        {
          "name": "Shortage Report (CSV)",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/reports/shortages?format=csv"
          }
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8123/api"
    },
    {
      "key": "access_token",
      "value": "your-token-here"
    }
  ]
}
```

---

## Changelog

### v1.0 (2024-10-10)
- ✅ Added shortage tracking endpoints
- ✅ Catalog lookup extended (barcode + SKU)
- ✅ Idempotency support
- ✅ CSV export
- ✅ Audit events

---

**API Version:** 1.0  
**Last Updated:** 2024-10-10  
**Base URL:** http://localhost:8123/api  
**Support:** api-support@magacin.com

