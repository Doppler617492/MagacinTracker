-- Pantheon ERP Integration Tables
-- Run this script to create all required tables manually

BEGIN;

-- =========================================================================
-- 1. ENHANCE ARTIKAL TABLE
-- =========================================================================
ALTER TABLE artikal ADD COLUMN IF NOT EXISTS supplier VARCHAR(255);
ALTER TABLE artikal ADD COLUMN IF NOT EXISTS article_class VARCHAR(64);
ALTER TABLE artikal ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE artikal ADD COLUMN IF NOT EXISTS time_chg_ts TIMESTAMP;
ALTER TABLE artikal ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP;
ALTER TABLE artikal ADD COLUMN IF NOT EXISTS source VARCHAR(32) DEFAULT 'PANTHEON';

CREATE INDEX IF NOT EXISTS ix_artikal_time_chg_ts ON artikal(time_chg_ts);

-- =========================================================================
-- 2. CREATE SUBJECTS TABLE
-- =========================================================================
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(32) NOT NULL,  -- supplier, customer, warehouse
    pib VARCHAR(32),
    address TEXT,
    city VARCHAR(128),
    postal_code VARCHAR(16),
    country VARCHAR(64),
    phone VARCHAR(32),
    email VARCHAR(128),
    aktivan BOOLEAN NOT NULL DEFAULT true,
    time_chg_ts TIMESTAMP,
    last_synced_at TIMESTAMP,
    source VARCHAR(32) NOT NULL DEFAULT 'PANTHEON',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_subjects_code ON subjects(code);
CREATE INDEX IF NOT EXISTS ix_subjects_type ON subjects(type);
CREATE INDEX IF NOT EXISTS ix_subjects_time_chg_ts ON subjects(time_chg_ts);

-- =========================================================================
-- 3. CREATE DOC_TYPES TABLE
-- =========================================================================
CREATE TABLE IF NOT EXISTS doc_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    direction VARCHAR(32) NOT NULL,  -- inbound, outbound
    aktivan BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_doc_types_code ON doc_types(code);
CREATE INDEX IF NOT EXISTS ix_doc_types_direction ON doc_types(direction);

-- =========================================================================
-- 4. CREATE RECEIPTS TABLE (Inbound Documents)
-- =========================================================================
CREATE TABLE IF NOT EXISTS receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_no VARCHAR(64) NOT NULL,
    doc_type_id UUID NOT NULL REFERENCES doc_types(id),
    date DATE NOT NULL,
    supplier_id UUID REFERENCES subjects(id),
    store_id UUID REFERENCES subjects(id),
    responsible_person VARCHAR(128),
    header_ref VARCHAR(64),
    notes TEXT,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(doc_no, doc_type_id, date)
);

CREATE INDEX IF NOT EXISTS ix_receipts_doc_no ON receipts(doc_no);
CREATE INDEX IF NOT EXISTS ix_receipts_date ON receipts(date);

-- =========================================================================
-- 5. CREATE RECEIPT_ITEMS TABLE
-- =========================================================================
CREATE TABLE IF NOT EXISTS receipt_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_id UUID NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    article_id UUID REFERENCES artikal(id),
    code VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    barcode VARCHAR(64),
    qty_requested NUMERIC(12, 3) NOT NULL DEFAULT 0,
    qty_completed NUMERIC(12, 3) NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'new',  -- new, partial, done
    reason_missing TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_receipt_items_receipt_id ON receipt_items(receipt_id);
CREATE INDEX IF NOT EXISTS ix_receipt_items_article_id ON receipt_items(article_id);
CREATE INDEX IF NOT EXISTS ix_receipt_items_code ON receipt_items(code);

-- =========================================================================
-- 6. CREATE DISPATCHES TABLE (Outbound Documents)
-- =========================================================================
CREATE TABLE IF NOT EXISTS dispatches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_no VARCHAR(64) NOT NULL,
    doc_type_id UUID NOT NULL REFERENCES doc_types(id),
    date DATE NOT NULL,
    warehouse_id UUID REFERENCES subjects(id),
    issuer VARCHAR(128),
    receiver VARCHAR(128),
    responsible_person VARCHAR(128),
    header_ref VARCHAR(64),
    notes TEXT,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(doc_no, doc_type_id, date)
);

CREATE INDEX IF NOT EXISTS ix_dispatches_doc_no ON dispatches(doc_no);
CREATE INDEX IF NOT EXISTS ix_dispatches_date ON dispatches(date);

-- =========================================================================
-- 7. CREATE DISPATCH_ITEMS TABLE (with exists_in_wms flag)
-- =========================================================================
CREATE TABLE IF NOT EXISTS dispatch_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispatch_id UUID NOT NULL REFERENCES dispatches(id) ON DELETE CASCADE,
    article_id UUID REFERENCES artikal(id),
    code VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    barcode VARCHAR(64),
    qty_requested NUMERIC(12, 3) NOT NULL DEFAULT 0,
    qty_completed NUMERIC(12, 3) NOT NULL DEFAULT 0,
    exists_in_wms BOOLEAN NOT NULL DEFAULT false,  -- CRITICAL: determines WMS task creation
    wms_flag BOOLEAN NOT NULL DEFAULT false,
    warehouse_code VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'new',  -- new, partial, done
    reason_missing TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_dispatch_items_dispatch_id ON dispatch_items(dispatch_id);
CREATE INDEX IF NOT EXISTS ix_dispatch_items_article_id ON dispatch_items(article_id);
CREATE INDEX IF NOT EXISTS ix_dispatch_items_code ON dispatch_items(code);
CREATE INDEX IF NOT EXISTS ix_dispatch_items_exists_in_wms ON dispatch_items(exists_in_wms);
CREATE INDEX IF NOT EXISTS ix_dispatch_items_warehouse_code ON dispatch_items(warehouse_code);

COMMIT;

-- =========================================================================
-- VERIFICATION
-- =========================================================================
SELECT 
  'subjects' as table_name, COUNT(*) as row_count FROM subjects
UNION ALL
SELECT 
  'doc_types' as table_name, COUNT(*) as row_count FROM doc_types
UNION ALL
SELECT 
  'receipts' as table_name, COUNT(*) as row_count FROM receipts
UNION ALL
SELECT 
  'receipt_items' as table_name, COUNT(*) as row_count FROM receipt_items
UNION ALL
SELECT 
  'dispatches' as table_name, COUNT(*) as row_count FROM dispatches
UNION ALL
SELECT 
  'dispatch_items' as table_name, COUNT(*) as row_count FROM dispatch_items;

