BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(30) NOT NULL CHECK (role IN ('admin', 'sales_rep', 'manager')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    import_type VARCHAR(30) NOT NULL CHECK (import_type IN ('customers', 'usage')),
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(30) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    total_rows INTEGER NOT NULL DEFAULT 0 CHECK (total_rows >= 0),
    inserted_rows INTEGER NOT NULL DEFAULT 0 CHECK (inserted_rows >= 0),
    updated_rows INTEGER NOT NULL DEFAULT 0 CHECK (updated_rows >= 0),
    failed_rows INTEGER NOT NULL DEFAULT 0 CHECK (failed_rows >= 0),
    error_details JSONB NOT NULL DEFAULT '[]'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    industry VARCHAR(100),
    account_owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    salesforce_account_id VARCHAR(100) UNIQUE,
    opportunity_stage VARCHAR(100),
    renewal_date DATE,
    status VARCHAR(30) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'pilot', 'inactive')),
    source_import_job_id UUID REFERENCES import_jobs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usage_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    snapshot_date DATE NOT NULL,
    active_users INTEGER NOT NULL CHECK (active_users >= 0),
    licensed_seats INTEGER CHECK (licensed_seats IS NULL OR licensed_seats >= 0),
    license_utilization NUMERIC(5, 2)
        CHECK (license_utilization IS NULL OR license_utilization BETWEEN 0 AND 100),
    usage_growth NUMERIC(7, 2),
    feature_adoption JSONB NOT NULL DEFAULT '{}'::JSONB,
    import_job_id UUID REFERENCES import_jobs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (customer_id, product_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS engagements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    engagement_type VARCHAR(30) NOT NULL,
    meeting_type VARCHAR(30),
    deliverable_type VARCHAR(30),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    notes TEXT,
    content JSONB NOT NULL DEFAULT '{}'::JSONB,
    input_snapshot JSONB NOT NULL DEFAULT '{}'::JSONB,
    model VARCHAR(100),
    prompt_version VARCHAR(50),
    status VARCHAR(30) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'saved', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS intelligence_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    next_best_actions JSONB NOT NULL DEFAULT '[]'::JSONB,
    ai_key_signal TEXT,
    last_interaction_at TIMESTAMPTZ,
    metrics JSONB NOT NULL DEFAULT '{}'::JSONB,
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    source_data_through TIMESTAMPTZ,
    generation_status VARCHAR(30) NOT NULL DEFAULT 'completed'
        CHECK (generation_status IN ('pending', 'completed', 'failed')),
    model VARCHAR(100),
    prompt_version VARCHAR(50),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Compatibility upgrades for databases created with an earlier version of
-- DealBrief AI. These statements are no-ops for a newly created database and
-- make this file safe to rerun as the single source of database structure.
ALTER TABLE engagements
    ADD COLUMN IF NOT EXISTS input_snapshot JSONB
        NOT NULL DEFAULT '{}'::JSONB,
    ADD COLUMN IF NOT EXISTS model VARCHAR(100),
    ADD COLUMN IF NOT EXISTS prompt_version VARCHAR(50),
    ADD COLUMN IF NOT EXISTS generated_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW();

ALTER TABLE customers
    ADD COLUMN IF NOT EXISTS source_import_job_id UUID
        REFERENCES import_jobs(id) ON DELETE SET NULL;

ALTER TABLE usage_snapshots
    ADD COLUMN IF NOT EXISTS import_job_id UUID
        REFERENCES import_jobs(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW();

ALTER TABLE intelligence_snapshots
    ADD COLUMN IF NOT EXISTS next_best_actions JSONB
        NOT NULL DEFAULT '[]'::JSONB,
    ADD COLUMN IF NOT EXISTS period_start TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS period_end TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS source_data_through TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS generation_status VARCHAR(30)
        NOT NULL DEFAULT 'completed';

-- Preserve a legacy single action in the structured array before removing the
-- obsolete next_best_action column from an existing database.
DO $migration$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'intelligence_snapshots'
          AND column_name = 'next_best_action'
    ) THEN
        UPDATE intelligence_snapshots
        SET next_best_actions = jsonb_build_array(
            jsonb_build_object(
                'action', next_best_action,
                'priority', 'high',
                'reason', COALESCE(ai_key_signal, ''),
                'dueDate', NULL
            )
        )
        WHERE next_best_action IS NOT NULL
          AND next_best_actions = '[]'::JSONB;

        ALTER TABLE intelligence_snapshots
            DROP COLUMN next_best_action;
    END IF;
END
$migration$;

-- Renewal date and active users come from customers and usage_snapshots.
-- Remove the obsolete AI-derived fields from an existing database.
ALTER TABLE intelligence_snapshots
    DROP COLUMN IF EXISTS renewal_risk,
    DROP COLUMN IF EXISTS expansion_signal;

CREATE INDEX IF NOT EXISTS idx_customers_active_name
    ON customers(name) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_usage_customer_date
    ON usage_snapshots(customer_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_engagements_customer_generated
    ON engagements(customer_id, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_intelligence_customer_generated
    ON intelligence_snapshots(customer_id, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_import_jobs_created
    ON import_jobs(created_at DESC);

COMMIT;
