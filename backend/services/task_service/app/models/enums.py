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
    
    # AI Intelligence Layer actions (Phase 4)
    AI_BIN_SUGGESTED = "AI_BIN_SUGGESTED"
    AI_BIN_ACCEPTED = "AI_BIN_ACCEPTED"
    AI_BIN_REJECTED = "AI_BIN_REJECTED"
    AI_RESTOCK_SUGGESTED = "AI_RESTOCK_SUGGESTED"
    AI_RESTOCK_APPROVED = "AI_RESTOCK_APPROVED"
    AI_RESTOCK_REJECTED = "AI_RESTOCK_REJECTED"
    AI_ANOMALY_DETECTED = "AI_ANOMALY_DETECTED"
    AI_ANOMALY_ACK = "AI_ANOMALY_ACK"
    AI_ANOMALY_RESOLVED = "AI_ANOMALY_RESOLVED"
    
    # IoT Integration Layer actions (Phase 5)
    RFID_EVENT_RECEIVED = "RFID_EVENT_RECEIVED"
    RFID_TAG_BOUND = "RFID_TAG_BOUND"
    RFID_TAG_UNBOUND = "RFID_TAG_UNBOUND"
    DOOR_COMMAND_ISSUED = "DOOR_COMMAND_ISSUED"
    DOOR_COMMAND_BLOCKED = "DOOR_COMMAND_BLOCKED"
    DOOR_AUTO_CLOSE = "DOOR_AUTO_CLOSE"
    PHOTO_ATTACHED = "PHOTO_ATTACHED"
    TELEMETRY_REPORTED = "TELEMETRY_REPORTED"
    TELEMETRY_ALERT_RAISED = "TELEMETRY_ALERT_RAISED"
    TELEMETRY_ALERT_ACKED = "TELEMETRY_ALERT_ACKED"
    VISION_COUNT_STARTED = "VISION_COUNT_STARTED"
    VISION_COUNT_SUBMITTED = "VISION_COUNT_SUBMITTED"
    VISION_COUNT_APPROVED = "VISION_COUNT_APPROVED"
    VISION_COUNT_REJECTED = "VISION_COUNT_REJECTED"
    
    # Vision AI & Robotics actions (Phase 7)
    VISION_ANALYZE = "VISION_ANALYZE"
    VISION_CONFIRMED = "VISION_CONFIRMED"
    VISION_DISCREPANCY = "VISION_DISCREPANCY"
    AMR_TASK_CREATED = "AMR_TASK_CREATED"
    AMR_TASK_ASSIGNED = "AMR_TASK_ASSIGNED"
    AMR_TASK_DONE = "AMR_TASK_DONE"
    AMR_TASK_ERROR = "AMR_TASK_ERROR"
    INDICATOR_ON = "INDICATOR_ON"
    INDICATOR_OFF = "INDICATOR_OFF"
    
    # Voice Picking & Global Control Room actions (Phase 8)
    VOICE_CONFIRM = "VOICE_CONFIRM"
    VOICE_RETRY = "VOICE_RETRY"
    VOICE_ERROR = "VOICE_ERROR"
    DEVICE_TELEMETRY_INGESTED = "DEVICE_TELEMETRY_INGESTED"
    DEVICE_OFFLINE_DETECTED = "DEVICE_OFFLINE_DETECTED"
    PREDICTIVE_ALERT_RAISED = "PREDICTIVE_ALERT_RAISED"
    PREDICTIVE_ALERT_ACK = "PREDICTIVE_ALERT_ACK"
    GLOBAL_OVERVIEW_ACCESSED = "GLOBAL_OVERVIEW_ACCESSED"


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


# ============================================================================
# RECEIVING (PRIJEM ROBE) - PHASE 2
# ============================================================================

class ReceivingStatus(str, Enum):
    """
    Receiving document status
    Serbian: Status prijema
    """
    NOVO = "novo"                          # New
    U_TOKU = "u_toku"                      # In progress
    ZAVRSENO = "završeno"                  # Completed (full)
    ZAVRSENO_DJELIMICNO = "završeno_djelimično"  # Completed (partial)


class ReceivingReason(str, Enum):
    """
    Reasons for receiving discrepancies
    Serbian: Razlog odstupanja u prijemu
    """
    MANJAK = "manjak"                      # Shortage
    VISAK = "višak"                        # Overage
    OSTECENO = "oštećeno"                  # Damaged
    NIJE_ISPORUCENO = "nije_isporučeno"    # Not delivered
    DRUGO = "drugo"                        # Other (custom reason)


class ReceivingItemStatus(str, Enum):
    """
    Receiving item status
    Serbian: Status stavke prijema
    """
    NOVO = "novo"          # New
    U_TOKU = "u_toku"      # In progress
    GOTOVO = "gotovo"      # Done


# ============================================================================
# LOCATION-BASED WMS - PHASE 3
# ============================================================================

class LocationType(str, Enum):
    """
    Location types in warehouse hierarchy
    Serbian: Tip lokacije (Zona → Regal → Polica → Bin)
    """
    ZONE = "zone"       # Zona (top-level area)
    REGAL = "regal"     # Regal (rack/aisle)
    POLICA = "polica"   # Polica (shelf)
    BIN = "bin"         # Bin (smallest storage unit)


class CycleCountStatus(str, Enum):
    """
    Cycle count status
    Serbian: Status popisa
    """
    SCHEDULED = "scheduled"      # Zakazano
    IN_PROGRESS = "in_progress"  # U toku
    COMPLETED = "completed"      # Završeno
    CANCELLED = "cancelled"      # Otkazano


# ============================================================================
# AI INTELLIGENCE LAYER - PHASE 4
# ============================================================================

class AnomalySeverity(str, Enum):
    """
    Anomaly severity levels
    Serbian: Nivo ozbiljnosti anomalije
    """
    LOW = "low"              # Niska
    MEDIUM = "medium"        # Srednja
    HIGH = "high"            # Visoka
    CRITICAL = "critical"    # Kritična


class AnomalyStatus(str, Enum):
    """
    Anomaly status
    Serbian: Status anomalije
    """
    NEW = "new"                          # Nova
    ACKNOWLEDGED = "acknowledged"        # Primljeno na znanje
    IN_PROGRESS = "in_progress"          # U obradi
    RESOLVED = "resolved"                # Rešeno
    FALSE_POSITIVE = "false_positive"    # Lažna dojava


# ============================================================================
# IOT INTEGRATION LAYER - PHASE 5
# ============================================================================

class RFIDEventType(str, Enum):
    """
    RFID event types
    Serbian: Tip RFID događaja
    """
    ENTRY = "entry"      # Ulaz
    EXIT = "exit"        # Izlaz
    READ = "read"        # Čitanje
    WRITE = "write"      # Pisanje


class DoorStatus(str, Enum):
    """
    Industrial door status
    Serbian: Status vrata
    """
    OPEN = "open"            # Otvoreno
    CLOSED = "closed"        # Zatvoreno
    OPENING = "opening"      # Otvara se
    CLOSING = "closing"      # Zatvara se
    STOPPED = "stopped"      # Zaustavljeno
    ERROR = "error"          # Greška


class TelemetryAlertSeverity(str, Enum):
    """
    Telemetry alert severity
    Serbian: Ozbiljnost alarma
    """
    INFO = "info"            # Informativno
    WARNING = "warning"      # Upozorenje
    CRITICAL = "critical"    # Kritično


# ============================================================================
# RFID LOCATIONS & LIVE MAP - PHASE 6
# ============================================================================

class ZoneType(str, Enum):
    """
    Warehouse zone types
    Serbian: Tip zone magacina
    """
    DOCK = "dock"                # Dok (prijem/otprema)
    CHILL = "chill"              # Hladnjača
    AISLE = "aisle"              # Prolaz/regal
    QUARANTINE = "quarantine"    # Karantin
    STAGING = "staging"          # Pripremna zona


class LocationTypeV2(str, Enum):
    """
    Location types (granular)
    Serbian: Tip lokacije (detaljno)
    """
    BIN = "bin"              # Bin/polica
    PALLET = "pallet"        # Paletno mesto
    FLOWRACK = "flowrack"    # Flow rack
    SHELF = "shelf"          # Shelf


class TagType(str, Enum):
    """
    Tag types for locations
    Serbian: Tip taga
    """
    RFID = "rfid"        # RFID EPC
    QR = "qr"            # QR kod
    BARCODE = "barcode"  # Barkod


class HandlingUnitType(str, Enum):
    """
    Handling unit types
    Serbian: Tip paletne jedinice
    """
    PALLET = "pallet"    # Paleta
    CARTON = "carton"    # Karton
    ROLL = "roll"        # Roll kontejner
    TOTE = "tote"        # Korpa


class HandlingUnitStatus(str, Enum):
    """
    Handling unit status
    Serbian: Status paletne jedinice
    """
    INBOUND = "inbound"      # Dolazna
    STAGED = "staged"        # Pripremljena
    STORED = "stored"        # Uskladištena
    PICKED = "picked"        # Pokupljena
    OUTBOUND = "outbound"    # Odlazna


# ============================================================================
# VISION AI & ROBOTICS - PHASE 7
# ============================================================================

class IndicatorType(str, Enum):
    """
    Location indicator types (Pick-to-Light / Put-to-Light)
    Serbian: Tip indikatora
    """
    PICK = "pick"            # Pick-to-Light (zeleno)
    PUT = "put"              # Put-to-Light (plavo)
    ALERT = "alert"          # Alarm (crveno)
    GUIDANCE = "guidance"    # Vodič (belo)


class IndicatorStatus(str, Enum):
    """
    Indicator status
    Serbian: Status indikatora
    """
    OFF = "off"          # Ugašeno
    ON = "on"            # Uključeno
    BLINK = "blink"      # Trepće
    ERROR = "error"      # Greška


class AMRTaskType(str, Enum):
    """
    AMR (Autonomous Mobile Robot) task types
    Serbian: Tip zadatka za robota
    """
    PICK = "pick"            # Izdavanje
    PUTAWAY = "putaway"      # Uskladištenje
    MOVE = "move"            # Premeštanje
    TRANSPORT = "transport"  # Transport


class AMRTaskStatus(str, Enum):
    """
    AMR task status
    Serbian: Status zadatka robota
    """
    PENDING = "pending"          # Na čekanju
    ASSIGNED = "assigned"        # Dodeljen
    IN_PROGRESS = "in_progress"  # U toku
    COMPLETED = "completed"      # Završen
    ERROR = "error"              # Greška
    CANCELLED = "cancelled"      # Otkazan


# ============================================================================
# VOICE PICKING & GLOBAL CONTROL ROOM - PHASE 8
# ============================================================================

class DeviceType(str, Enum):
    """
    Device types for health monitoring
    Serbian: Tip uređaja
    """
    SCANNER = "scanner"              # Skener (Zebra)
    CAMERA = "camera"                # Kamera
    DOOR_CONTROLLER = "door_controller"  # Kontroler vrata
    EDGE_GATEWAY = "edge_gateway"    # Edge gateway
    INDICATOR = "indicator"          # LED indikator
    AMR = "amr"                      # Autonomni robot


class PredictiveAlertStatus(str, Enum):
    """
    Predictive maintenance alert status
    Serbian: Status prediktivnog upozorenja
    """
    NEW = "new"                          # Novo
    ACKNOWLEDGED = "acknowledged"        # Primljeno na znanje
    RESOLVED = "resolved"                # Rešeno
    FALSE_POSITIVE = "false_positive"    # Lažna dojava
