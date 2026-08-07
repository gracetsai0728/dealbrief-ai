BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(30) NOT NULL CHECK (role IN ('user', 'admin', 'sales_rep', 'manager')),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    industry VARCHAR(100),
    status VARCHAR(30) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'pilot', 'inactive')),
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

DO $migration$
BEGIN
    IF to_regclass('subscriptions') IS NULL
       AND to_regclass('usage_snapshots') IS NOT NULL THEN
        ALTER TABLE usage_snapshots RENAME TO subscriptions;
    END IF;
END
$migration$;

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    subscription_start_date DATE NOT NULL,
    subscription_end_date DATE,
    subscription_status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (subscription_status IN ('active', 'expired', 'canceled')),
    licensed_seats INTEGER CHECK (licensed_seats IS NULL OR licensed_seats >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (customer_id, product_id, subscription_start_date)
);

CREATE TABLE IF NOT EXISTS intelligence_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    recommended_next_steps JSONB NOT NULL DEFAULT '{}'::JSONB,
    industry_dynamics JSONB NOT NULL DEFAULT '[]'::JSONB,
    company_news JSONB NOT NULL DEFAULT '[]'::JSONB,
    ai_key_signal TEXT,
    metrics JSONB NOT NULL DEFAULT '{}'::JSONB,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Compatibility upgrades for databases created with an earlier version of
-- DealBrief AI. These statements are no-ops for a newly created database and
-- make this file safe to rerun as the single source of database structure.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

UPDATE users
SET password_hash = 'scrypt:32768:8:1$cNHmqUsTZl9HEvQu$bd6a1978e46978f85c1c77cee1cc3b3cb312d17d3798fcb36f0d566036c8de08b80c7957a0fb5bbbaeb8ecba99607fe50fd7a5f6e69d45cd9d86340a24293a59'
WHERE password_hash IS NULL;

ALTER TABLE users
    ALTER COLUMN password_hash SET NOT NULL;

ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users
    ADD CONSTRAINT users_role_check
    CHECK (role IN ('user', 'admin', 'sales_rep', 'manager'));

ALTER TABLE subscriptions
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ
        NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS subscription_start_date DATE,
    ADD COLUMN IF NOT EXISTS subscription_end_date DATE,
    ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(20)
        NOT NULL DEFAULT 'active';

DO $migration$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'subscriptions'
          AND column_name = 'snapshot_date'
    ) THEN
        UPDATE subscriptions
        SET subscription_start_date = snapshot_date
        WHERE subscription_start_date IS NULL;
    END IF;
END
$migration$;

ALTER TABLE subscriptions
    ALTER COLUMN subscription_start_date SET NOT NULL;

ALTER TABLE subscriptions
    DROP CONSTRAINT IF EXISTS usage_snapshots_customer_id_product_id_snapshot_date_key;
ALTER TABLE subscriptions
    DROP CONSTRAINT IF EXISTS usage_snapshot_unique;
ALTER TABLE subscriptions
    DROP CONSTRAINT IF EXISTS usage_snapshots_subscription_status_check;
ALTER TABLE subscriptions
    DROP CONSTRAINT IF EXISTS subscriptions_subscription_status_check;
ALTER TABLE subscriptions
    ADD CONSTRAINT subscriptions_subscription_status_check
        CHECK (subscription_status IN ('active', 'expired', 'canceled'));
DROP INDEX IF EXISTS uq_usage_customer_product_subscription;
CREATE UNIQUE INDEX IF NOT EXISTS uq_subscription_customer_product_start
    ON subscriptions(customer_id, product_id, subscription_start_date);

DO $migration$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'intelligence_snapshots'
          AND column_name = 'next_best_actions'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'intelligence_snapshots'
          AND column_name = 'recommended_next_steps'
    ) THEN
        ALTER TABLE intelligence_snapshots
            RENAME COLUMN next_best_actions TO recommended_next_steps;
    END IF;
END
$migration$;

ALTER TABLE intelligence_snapshots
    ADD COLUMN IF NOT EXISTS recommended_next_steps JSONB
        NOT NULL DEFAULT '{}'::JSONB,
    ADD COLUMN IF NOT EXISTS industry_dynamics JSONB
        NOT NULL DEFAULT '[]'::JSONB,
    ADD COLUMN IF NOT EXISTS company_news JSONB
        NOT NULL DEFAULT '[]'::JSONB;

UPDATE intelligence_snapshots
SET recommended_next_steps = '{}'::JSONB
WHERE jsonb_typeof(recommended_next_steps) <> 'object';

ALTER TABLE intelligence_snapshots
    DROP COLUMN IF EXISTS last_interaction_at,
    DROP COLUMN IF EXISTS next_best_action,
    DROP COLUMN IF EXISTS snapshot_date,
    DROP COLUMN IF EXISTS model,
    DROP COLUMN IF EXISTS prompt_version,
    DROP COLUMN IF EXISTS period_start,
    DROP COLUMN IF EXISTS period_end,
    DROP COLUMN IF EXISTS source_data_through,
    DROP COLUMN IF EXISTS generation_status;

-- Remove obsolete fields from existing databases.
DROP INDEX IF EXISTS idx_subscription_usage_points_date;
DROP INDEX IF EXISTS idx_usage_customer_date;
DROP INDEX IF EXISTS idx_subscriptions_customer_date;
ALTER TABLE customers
    DROP COLUMN IF EXISTS opportunity_stage,
    DROP COLUMN IF EXISTS renewal_date,
    DROP COLUMN IF EXISTS account_owner_id,
    DROP COLUMN IF EXISTS salesforce_account_id;
ALTER TABLE subscriptions
    DROP COLUMN IF EXISTS active_users,
    DROP COLUMN IF EXISTS license_utilization,
    DROP COLUMN IF EXISTS usage_growth,
    DROP COLUMN IF EXISTS feature_adoption,
    DROP COLUMN IF EXISTS snapshot_date;
DROP TABLE IF EXISTS subscription_usage_points;

ALTER TABLE intelligence_snapshots
    DROP COLUMN IF EXISTS renewal_risk,
    DROP COLUMN IF EXISTS expansion_signal;

CREATE INDEX IF NOT EXISTS idx_customers_active_name
    ON customers(name) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_subscriptions_customer_start
    ON subscriptions(customer_id, subscription_start_date DESC);
CREATE INDEX IF NOT EXISTS idx_intelligence_customer_generated
    ON intelligence_snapshots(customer_id, generated_at DESC);
ALTER TABLE customers
    DROP COLUMN IF EXISTS source_import_job_id;
ALTER TABLE subscriptions
    DROP COLUMN IF EXISTS import_job_id;
DROP TABLE IF EXISTS import_jobs;
DROP TABLE IF EXISTS engagements;

COMMIT;
