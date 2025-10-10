from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    MENADZER = "MENADZER"
    SEF = "SEF"
    KOMERCIJALISTA = "KOMERCIJALISTA"
    MAGACIONER = "MAGACIONER"


class TrebovanjeStatus(str, Enum):
    new = "new"
    assigned = "assigned"
    in_progress = "in_progress"
    done = "done"
    failed = "failed"


class TrebovanjeItemStatus(str, Enum):
    new = "new"
    assigned = "assigned"
    in_progress = "in_progress"
    done = "done"


class ZaduznicaStatus(str, Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    done = "done"
    blocked = "blocked"


class ZaduznicaItemStatus(str, Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    done = "done"


class TaskPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"


class ImportStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class ScanResult(str, Enum):
    match = "match"
    mismatch = "mismatch"
    duplicate = "duplicate"


class DiscrepancyStatus(str, Enum):
    none = "none"
    short_pick = "short_pick"
    not_found = "not_found"
    damaged = "damaged"
    wrong_barcode = "wrong_barcode"


class AuditAction(str, Enum):
    # Authentication actions
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_RESET = "PASSWORD_RESET"
    USER_CREATED = "USER_CREATED"
    USER_ROLE_CHANGED = "USER_ROLE_CHANGED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    
    # Business actions
    import_created = "import.created"
    trebovanje_imported = "trebovanje.imported"
    zaduznica_assigned = "zaduznica.assigned"
    zaduznica_reassigned = "zaduznica.reassigned"
    scan_recorded = "scan.recorded"
    manual_complete = "manual.complete"
    scheduler_suggested = "scheduler.suggested"
    scheduler_accepted = "scheduler.accepted"
    scheduler_override = "scheduler.override"
    catalog_sync = "catalog.sync"
    catalog_enriched = "catalog.enriched"
    catalog_manual_update = "catalog.manual_update"
    
    # Shortage tracking actions
    SCAN_OK = "SCAN_OK"
    SCAN_MISMATCH = "SCAN_MISMATCH"
    SHORT_PICK_RECORDED = "SHORT_PICK_RECORDED"
    NOT_FOUND_RECORDED = "NOT_FOUND_RECORDED"
    DOC_COMPLETED_INCOMPLETE = "DOC_COMPLETED_INCOMPLETE"
    LOOKUP_BY_CODE = "LOOKUP_BY_CODE"


class SchedulerLogStatus(str, Enum):
    suggested = "suggested"
    accepted = "accepted"
    override = "override"
