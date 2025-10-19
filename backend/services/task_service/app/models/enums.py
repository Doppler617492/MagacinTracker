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


class PartialCompletionReason(str, Enum):
    """
    Reasons for partial completion (Manhattan-style exception handling)
    Serbian: Razlog za djelimično završen zadatak
    """
    NEMA_NA_STANJU = "nema_na_stanju"          # Out of stock
    OSTECENO = "osteceno"                      # Damaged
    NIJE_PRONAĐENO = "nije_pronađeno"          # Not found
    KRIVI_ARTIKAL = "krivi_artikal"            # Wrong article
    DRUGO = "drugo"                            # Other (custom reason)


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
    trebovanje_deleted = "trebovanje.deleted"
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
    
    # Manual quantity entry actions
    MANUAL_QTY_SAVED = "MANUAL_QTY_SAVED"
    ITEM_PARTIAL = "ITEM_PARTIAL"
    ITEM_CLOSED = "ITEM_CLOSED"
    DOC_COMPLETED_PARTIAL = "DOC_COMPLETED_PARTIAL"
    DOC_COMPLETED_FULL = "DOC_COMPLETED_FULL"


class SchedulerLogStatus(str, Enum):
    suggested = "suggested"
    accepted = "accepted"
    override = "override"


# ============================================================================
# PANTHEON ERP INTEGRATION ENUMS
# ============================================================================

class SubjectType(str, Enum):
    """Subject/Partner type classification"""
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    WAREHOUSE = "warehouse"


class DocumentDirection(str, Enum):
    """Document direction (inbound/outbound)"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class DocumentItemStatus(str, Enum):
    """Document item processing status"""
    NEW = "new"
    PARTIAL = "partial"
    DONE = "done"


class SyncAction(str, Enum):
    """Pantheon sync audit actions"""
    CATALOG_SYNC = "CATALOG_SYNC"
    SUBJECTS_SYNC = "SUBJECTS_SYNC"
    ISSUE_SYNC = "ISSUE_SYNC"
    RECEIPT_SYNC = "RECEIPT_SYNC"
    CATALOG_LOOKUP_API = "CATALOG_LOOKUP_API"
    WMS_FLAG_SET = "WMS_FLAG_SET"
