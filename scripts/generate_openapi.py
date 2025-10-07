#!/usr/bin/env python
"""Generate OpenAPI JSON for API Gateway."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from services.api_gateway.app.main import app  # noqa: E402

output_path = REPO_ROOT / "docs" / "openapi" / "api-gateway.json"
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8") as handle:
    json.dump(app.openapi(), handle, ensure_ascii=False, indent=2)

print(f"OpenAPI spec written to {output_path}")
