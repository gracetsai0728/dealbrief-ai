BEGIN;

INSERT INTO users (id, name, email, role)
VALUES
    ('10000000-0000-0000-0000-000000000001', 'Grace Lin', 'grace.lin@example.com', 'admin'),
    ('10000000-0000-0000-0000-000000000002', 'Maya Chen', 'maya.chen@example.com', 'sales_rep'),
    ('10000000-0000-0000-0000-000000000003', 'Jordan Patel', 'jordan.patel@example.com', 'manager')
ON CONFLICT (email) DO UPDATE
SET name = EXCLUDED.name,
    role = EXCLUDED.role;

INSERT INTO products (id, name, description, status)
VALUES
    ('20000000-0000-0000-0000-000000000001', 'CRM Platform', 'Pipeline, account, and sales workflow management.', 'active'),
    ('20000000-0000-0000-0000-000000000002', 'Collaboration Tool', 'Team collaboration and workflow coordination.', 'active'),
    ('20000000-0000-0000-0000-000000000003', 'Business Analytics Software', 'Dashboards, reporting, and forecasting analytics.', 'active')
ON CONFLICT (name) DO UPDATE
SET description = EXCLUDED.description,
    status = EXCLUDED.status;

INSERT INTO customers (
    id, name, industry, account_owner_id, salesforce_account_id,
    opportunity_stage, renewal_date, status, created_at, updated_at
)
VALUES
    (
        '30000000-0000-0000-0000-000000000001', 'ABC Bank', 'Financial Services',
        (SELECT id FROM users WHERE email = 'grace.lin@example.com'),
        'SF-ACCT-1042', 'Renewal Review', '2026-10-15', 'active', NOW(), NOW()
    ),
    (
        '30000000-0000-0000-0000-000000000002', 'Northstar Retail', 'Retail',
        (SELECT id FROM users WHERE email = 'maya.chen@example.com'),
        'SF-ACCT-2088', 'Expansion', '2026-12-01', 'active', NOW(), NOW()
    ),
    (
        '30000000-0000-0000-0000-000000000003', 'GreenHealth Group', 'Healthcare',
        (SELECT id FROM users WHERE email = 'jordan.patel@example.com'),
        'SF-ACCT-3175', 'Discovery', '2027-01-20', 'pilot', NOW(), NOW()
    )
ON CONFLICT (salesforce_account_id) DO UPDATE
SET name = EXCLUDED.name,
    industry = EXCLUDED.industry,
    account_owner_id = EXCLUDED.account_owner_id,
    opportunity_stage = EXCLUDED.opportunity_stage,
    renewal_date = EXCLUDED.renewal_date,
    status = EXCLUDED.status,
    deleted_at = NULL,
    updated_at = NOW();

INSERT INTO usage_snapshots (
    id, customer_id, product_id, snapshot_date, active_users, licensed_seats,
    license_utilization, usage_growth, feature_adoption
)
VALUES
    (
        '40000000-0000-0000-0000-000000000001',
        (SELECT id FROM customers WHERE salesforce_account_id = 'SF-ACCT-1042'),
        (SELECT id FROM products WHERE name = 'CRM Platform'),
        '2026-07-04', 410, 500, 82.00, 35.00,
        '{"Reporting": 58, "Automation": 42}'::JSONB
    ),
    (
        '40000000-0000-0000-0000-000000000002',
        (SELECT id FROM customers WHERE salesforce_account_id = 'SF-ACCT-2088'),
        (SELECT id FROM products WHERE name = 'Collaboration Tool'),
        '2026-07-05', 780, 857, 91.02, 48.00,
        '{"Channels": 88, "Workflow approvals": 63}'::JSONB
    ),
    (
        '40000000-0000-0000-0000-000000000003',
        (SELECT id FROM customers WHERE salesforce_account_id = 'SF-ACCT-3175'),
        (SELECT id FROM products WHERE name = 'Business Analytics Software'),
        '2026-07-03', 145, 227, 63.88, 18.00,
        '{"Dashboards": 51, "Forecasting": 24}'::JSONB
    )
ON CONFLICT (customer_id, product_id, snapshot_date) DO UPDATE
SET active_users = EXCLUDED.active_users,
    licensed_seats = EXCLUDED.licensed_seats,
    license_utilization = EXCLUDED.license_utilization,
    usage_growth = EXCLUDED.usage_growth,
    feature_adoption = EXCLUDED.feature_adoption;

INSERT INTO intelligence_snapshots (
    id, customer_id, snapshot_date, next_best_actions, ai_key_signal,
    last_interaction_at,
    metrics, period_start, period_end, source_data_through,
    generation_status, model, prompt_version, generated_at
)
VALUES (
    '50000000-0000-0000-0000-000000000001',
    (SELECT id FROM customers WHERE salesforce_account_id = 'SF-ACCT-1042'),
    '2026-07-05',
    '[
      {
        "action": "Prepare renewal value story",
        "priority": "high",
        "reason": "Usage is growing, but reporting adoption remains uneven.",
        "dueDate": null
      },
      {
        "action": "Validate reporting adoption blockers",
        "priority": "medium",
        "reason": "Reporting adoption is lower than overall license utilization.",
        "dueDate": null
      }
    ]'::JSONB,
    'Strong CRM adoption is offset by uneven advanced reporting usage.',
    '2026-07-02T17:00:00Z',
    '{
      "accountHealthScore": 74,
      "adoptionScore": 70,
      "engagementScore": 72,
      "usageGrowth": 35,
      "licenseUtilization": 82,
      "riskReasons": ["Uneven reporting adoption"]
    }'::JSONB,
    '2026-04-06T00:00:00Z',
    '2026-07-05T23:59:59Z',
    '2026-07-05T23:59:59Z',
    'completed',
    'seed-data',
    'seed-v1',
    '2026-07-05T23:59:59Z'
)
ON CONFLICT (id) DO UPDATE
SET next_best_actions = EXCLUDED.next_best_actions,
    ai_key_signal = EXCLUDED.ai_key_signal,
    metrics = EXCLUDED.metrics;

INSERT INTO engagements (
    id, customer_id, product_id, created_by, engagement_type, meeting_type,
    deliverable_type, occurred_at, title, summary, notes, content,
    input_snapshot, model, prompt_version, status, generated_at
)
VALUES (
    '60000000-0000-0000-0000-000000000001',
    (SELECT id FROM customers WHERE salesforce_account_id = 'SF-ACCT-1042'),
    (SELECT id FROM products WHERE name = 'CRM Platform'),
    (SELECT id FROM users WHERE email = 'grace.lin@example.com'),
    'generated_brief',
    'qbr',
    'call_brief',
    '2026-07-02T17:00:00Z',
    'ABC Bank QBR Call Brief',
    'QBR preparation focused on proving renewal value and addressing uneven reporting adoption.',
    'Focus on renewal value.',
    '{"title": "ABC Bank QBR Call Brief", "summary": "QBR preparation focused on proving renewal value and addressing uneven reporting adoption."}'::JSONB,
    '{"source": "seed demonstration record"}'::JSONB,
    'seed-data',
    'seed-v1',
    'saved',
    '2026-07-02T17:00:00Z'
)
ON CONFLICT (id) DO UPDATE
SET summary = EXCLUDED.summary,
    status = EXCLUDED.status,
    updated_at = NOW();

COMMIT;
