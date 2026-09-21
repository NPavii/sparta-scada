-- Sparta SCADA service tables
-- Applied automatically by PostgreSQL on first container start.

CREATE TABLE IF NOT EXISTS work_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_code TEXT NOT NULL,
    equipment_name TEXT,
    title TEXT NOT NULL,
    description TEXT,
    priority INTEGER NOT NULL DEFAULT 3,
    status TEXT NOT NULL DEFAULT 'pending',
    external_id TEXT,
    external_status TEXT,
    trigger_channel INTEGER,
    trigger_condition TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_work_orders_equipment_code ON work_orders(equipment_code);
CREATE INDEX IF NOT EXISTS idx_work_orders_external_id ON work_orders(external_id);

CREATE TABLE IF NOT EXISTS work_order_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_order_id UUID NOT NULL REFERENCES work_orders(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_work_order_status_history_order_id ON work_order_status_history(work_order_id);
