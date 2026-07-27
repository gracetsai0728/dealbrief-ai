-- Run once in pgAdmin if the engagements table was created before the
-- OpenAI-backed MVP fields were added. Safe to run more than once.

ALTER TABLE engagements
ADD COLUMN IF NOT EXISTS input_snapshot JSONB
    NOT NULL DEFAULT '{}'::JSONB;

ALTER TABLE engagements
ADD COLUMN IF NOT EXISTS model VARCHAR(100);

ALTER TABLE engagements
ADD COLUMN IF NOT EXISTS prompt_version VARCHAR(50);

ALTER TABLE engagements
ADD COLUMN IF NOT EXISTS generated_at TIMESTAMPTZ
    NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_engagements_customer_generated
    ON engagements(customer_id, generated_at DESC);

CREATE TABLE IF NOT EXISTS import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    import_type VARCHAR(30) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(30) NOT NULL,
    total_rows INTEGER NOT NULL DEFAULT 0,
    inserted_rows INTEGER NOT NULL DEFAULT 0,
    updated_rows INTEGER NOT NULL DEFAULT 0,
    failed_rows INTEGER NOT NULL DEFAULT 0,
    error_details JSONB NOT NULL DEFAULT '[]'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

ALTER TABLE customers
ADD COLUMN IF NOT EXISTS source_import_job_id UUID
    REFERENCES import_jobs(id) ON DELETE SET NULL;

ALTER TABLE usage_snapshots
ADD COLUMN IF NOT EXISTS import_job_id UUID
    REFERENCES import_jobs(id) ON DELETE SET NULL;

ALTER TABLE usage_snapshots
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ
    NOT NULL DEFAULT NOW();

ALTER TABLE intelligence_snapshots
ADD COLUMN IF NOT EXISTS next_best_actions JSONB
    NOT NULL DEFAULT '[]'::JSONB;

ALTER TABLE intelligence_snapshots
ADD COLUMN IF NOT EXISTS period_start TIMESTAMPTZ;

ALTER TABLE intelligence_snapshots
ADD COLUMN IF NOT EXISTS period_end TIMESTAMPTZ;

ALTER TABLE intelligence_snapshots
ADD COLUMN IF NOT EXISTS source_data_through TIMESTAMPTZ;

ALTER TABLE intelligence_snapshots
ADD COLUMN IF NOT EXISTS generation_status VARCHAR(30)
    NOT NULL DEFAULT 'completed';

CREATE INDEX IF NOT EXISTS idx_usage_customer_date
    ON usage_snapshots(customer_id, snapshot_date DESC);

CREATE INDEX IF NOT EXISTS idx_intelligence_customer_generated
    ON intelligence_snapshots(customer_id, generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_import_jobs_created
    ON import_jobs(created_at DESC);
