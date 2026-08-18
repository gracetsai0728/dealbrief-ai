BEGIN;

INSERT INTO users (id, name, email, role, password_hash, is_active)
VALUES
    (
        '10000000-0000-0000-0000-000000000001', 'Grace Lin',
        'grace.lin@example.com', 'admin',
        'scrypt:32768:8:1$iSmTwyRt9mqMUXF0$383ea55f5b71983d4ab65df38568c2de54d89233eff8657e41eeb4310f59e85145b4c8aeb457238660d7586ee18c7a953b817d879bc5a2b4d285b862130fee2a',
        TRUE
    ),
    (
        '10000000-0000-0000-0000-000000000002', 'Maya Chen',
        'maya.chen@example.com', 'sales_rep',
        'scrypt:32768:8:1$cNHmqUsTZl9HEvQu$bd6a1978e46978f85c1c77cee1cc3b3cb312d17d3798fcb36f0d566036c8de08b80c7957a0fb5bbbaeb8ecba99607fe50fd7a5f6e69d45cd9d86340a24293a59',
        TRUE
    ),
    (
        '10000000-0000-0000-0000-000000000003', 'Jordan Patel',
        'jordan.patel@example.com', 'manager',
        'scrypt:32768:8:1$cNHmqUsTZl9HEvQu$bd6a1978e46978f85c1c77cee1cc3b3cb312d17d3798fcb36f0d566036c8de08b80c7957a0fb5bbbaeb8ecba99607fe50fd7a5f6e69d45cd9d86340a24293a59',
        TRUE
    ),
    (
        '10000000-0000-0000-0000-000000000004', 'Demo User',
        'user@dealbrief.ai', 'user',
        'scrypt:32768:8:1$cNHmqUsTZl9HEvQu$bd6a1978e46978f85c1c77cee1cc3b3cb312d17d3798fcb36f0d566036c8de08b80c7957a0fb5bbbaeb8ecba99607fe50fd7a5f6e69d45cd9d86340a24293a59',
        TRUE
    ),
    (
        '10000000-0000-0000-0000-000000000005', 'Demo Admin',
        'admin@dealbrief.ai', 'admin',
        'scrypt:32768:8:1$iSmTwyRt9mqMUXF0$383ea55f5b71983d4ab65df38568c2de54d89233eff8657e41eeb4310f59e85145b4c8aeb457238660d7586ee18c7a953b817d879bc5a2b4d285b862130fee2a',
        TRUE
    )
ON CONFLICT (email) DO UPDATE
SET name = EXCLUDED.name,
    role = EXCLUDED.role,
    password_hash = EXCLUDED.password_hash,
    is_active = EXCLUDED.is_active;

INSERT INTO products (id, name, description, status)
VALUES
    ('20000000-0000-0000-0000-000000000001', 'CRM Platform', 'Pipeline, account, and sales workflow management.', 'active'),
    ('20000000-0000-0000-0000-000000000002', 'Collaboration Tool', 'Team collaboration and workflow coordination.', 'active'),
    ('20000000-0000-0000-0000-000000000003', 'Business Analytics Software', 'Dashboards, reporting, and forecasting analytics.', 'active')
ON CONFLICT (name) DO UPDATE
SET description = EXCLUDED.description,
    status = EXCLUDED.status;

INSERT INTO customers (
    id, name, industry, status, created_at, updated_at
)
SELECT
    seed.id::UUID,
    seed.name,
    seed.industry,
    seed.status,
    NOW(),
    NOW()
FROM (
    VALUES
        ('30000000-0000-0000-0000-000000000001', 'ABC Bank', 'Financial Services', 'active'),
        ('30000000-0000-0000-0000-000000000002', 'Northstar Retail', 'Retail', 'active'),
        ('30000000-0000-0000-0000-000000000003', 'GreenHealth Group', 'Healthcare', 'pilot'),
        ('30000000-0000-0000-0000-000000000004', 'Summit Manufacturing', 'Manufacturing', 'active'),
        ('30000000-0000-0000-0000-000000000005', 'BrightPath Education', 'Education', 'active')
) AS seed(id, name, industry, status)
WHERE NOT EXISTS (
    SELECT 1
    FROM customers AS existing
    WHERE LOWER(existing.name) = LOWER(seed.name)
)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    industry = EXCLUDED.industry,
    status = EXCLUDED.status,
    deleted_at = NULL,
    updated_at = NOW();

UPDATE customers AS customer
SET industry = seed.industry,
    status = seed.status,
    deleted_at = NULL,
    updated_at = NOW()
FROM (
    VALUES
        ('ABC Bank', 'Financial Services', 'active'),
        ('Northstar Retail', 'Retail', 'active'),
        ('GreenHealth Group', 'Healthcare', 'pilot'),
        ('Summit Manufacturing', 'Manufacturing', 'active'),
        ('BrightPath Education', 'Education', 'active')
) AS seed(name, industry, status)
WHERE LOWER(customer.name) = LOWER(seed.name);

DELETE FROM subscriptions
WHERE customer_id IN (
    SELECT id
    FROM customers
    WHERE name IN (
        'ABC Bank', 'Northstar Retail', 'GreenHealth Group',
        'Summit Manufacturing', 'BrightPath Education'
    )
);

INSERT INTO subscriptions (
    id, customer_id, product_id, subscription_start_date,
    subscription_end_date, subscription_status, licensed_seats
)
VALUES
    (
        '40000000-0000-0000-0000-000000000001',
        (SELECT id FROM customers WHERE name = 'ABC Bank'),
        (SELECT id FROM products WHERE name = 'CRM Platform'),
        '2026-01-01', '2026-12-31', 'active', 500
    ),
    (
        '40000000-0000-0000-0000-000000000003',
        (SELECT id FROM customers WHERE name = 'Northstar Retail'),
        (SELECT id FROM products WHERE name = 'Collaboration Tool'),
        '2026-02-01', '2027-01-31', 'active', 857
    ),
    (
        '40000000-0000-0000-0000-000000000004',
        (SELECT id FROM customers WHERE name = 'Northstar Retail'),
        (SELECT id FROM products WHERE name = 'Business Analytics Software'),
        '2026-04-01', '2027-03-31', 'active', 600
    ),
    (
        '40000000-0000-0000-0000-000000000006',
        (SELECT id FROM customers WHERE name = 'GreenHealth Group'),
        (SELECT id FROM products WHERE name = 'CRM Platform'),
        '2026-06-01', '2027-05-31', 'active', 200
    ),
    (
        '40000000-0000-0000-0000-000000000007',
        (SELECT id FROM customers WHERE name = 'Summit Manufacturing'),
        (SELECT id FROM products WHERE name = 'CRM Platform'),
        '2026-01-15', '2027-01-14', 'active', 300
    ),
    (
        '40000000-0000-0000-0000-000000000008',
        (SELECT id FROM customers WHERE name = 'Summit Manufacturing'),
        (SELECT id FROM products WHERE name = 'Business Analytics Software'),
        '2026-02-15', '2027-02-14', 'active', 250
    ),
    (
        '40000000-0000-0000-0000-000000000009',
        (SELECT id FROM customers WHERE name = 'BrightPath Education'),
        (SELECT id FROM products WHERE name = 'Collaboration Tool'),
        '2026-03-15', '2027-03-14', 'active', 500
    ),
    (
        '40000000-0000-0000-0000-000000000011',
        (SELECT id FROM customers WHERE name = 'ABC Bank'),
        (SELECT id FROM products WHERE name = 'Business Analytics Software'),
        '2026-05-01', '2027-04-30', 'active', 300
    ),
    (
        '40000000-0000-0000-0000-000000000012',
        (SELECT id FROM customers WHERE name = 'Northstar Retail'),
        (SELECT id FROM products WHERE name = 'CRM Platform'),
        '2026-01-10', '2027-01-09', 'active', 700
    ),
    (
        '40000000-0000-0000-0000-000000000015',
        (SELECT id FROM customers WHERE name = 'BrightPath Education'),
        (SELECT id FROM products WHERE name = 'Business Analytics Software'),
        '2026-02-20', '2027-02-19', 'active', 425
    )
ON CONFLICT (customer_id, product_id, subscription_start_date) DO UPDATE
SET licensed_seats = EXCLUDED.licensed_seats,
    subscription_end_date = EXCLUDED.subscription_end_date,
    subscription_status = EXCLUDED.subscription_status;

-- Add realistic annual renewal history for each customer's selected products.
-- The portfolios intentionally vary from one to three products. CRM histories
-- span five years, Collaboration four, and Analytics three. Seat packages
-- generally expand at renewal, with one flat renewal and one small contraction.
WITH renewal_history (product_name, years_back, seat_factor) AS (
    VALUES
        ('CRM Platform', 4, 0.60::NUMERIC),
        ('CRM Platform', 3, 0.68::NUMERIC),
        ('CRM Platform', 2, 0.78::NUMERIC),
        ('CRM Platform', 1, 0.89::NUMERIC),
        ('Collaboration Tool', 3, 0.66::NUMERIC),
        ('Collaboration Tool', 2, 0.78::NUMERIC),
        ('Collaboration Tool', 1, 0.90::NUMERIC),
        ('Business Analytics Software', 2, 0.76::NUMERIC),
        ('Business Analytics Software', 1, 0.89::NUMERIC)
),
current_seed_subscriptions AS (
    SELECT
        subscription.*,
        product.name AS product_name,
        customer.name AS customer_name
    FROM subscriptions AS subscription
    JOIN products AS product ON product.id = subscription.product_id
    JOIN customers AS customer ON customer.id = subscription.customer_id
    WHERE subscription.id IN (
        '40000000-0000-0000-0000-000000000001',
        '40000000-0000-0000-0000-000000000003',
        '40000000-0000-0000-0000-000000000004',
        '40000000-0000-0000-0000-000000000006',
        '40000000-0000-0000-0000-000000000007',
        '40000000-0000-0000-0000-000000000008',
        '40000000-0000-0000-0000-000000000009',
        '40000000-0000-0000-0000-000000000011',
        '40000000-0000-0000-0000-000000000012',
        '40000000-0000-0000-0000-000000000015'
    )
)
INSERT INTO subscriptions (
    id, customer_id, product_id, subscription_start_date,
    subscription_end_date, subscription_status, licensed_seats
)
SELECT
    gen_random_uuid(),
    current_subscription.customer_id,
    current_subscription.product_id,
    (
        current_subscription.subscription_start_date
        - make_interval(years => history.years_back)
    )::DATE,
    (
        current_subscription.subscription_start_date
        - make_interval(years => history.years_back - 1)
        - INTERVAL '1 day'
    )::DATE,
    'expired',
    GREATEST(
        5,
        (
            ROUND(
                current_subscription.licensed_seats
                * CASE
                    WHEN current_subscription.customer_name = 'BrightPath Education'
                         AND current_subscription.product_name = 'Collaboration Tool'
                         AND history.years_back = 1
                        THEN 1.00
                    WHEN current_subscription.customer_name = 'Summit Manufacturing'
                         AND current_subscription.product_name = 'Business Analytics Software'
                         AND history.years_back = 1
                        THEN 1.04
                    ELSE history.seat_factor
                  END
                / 5.0
            ) * 5
        )::INTEGER
    )
FROM current_seed_subscriptions AS current_subscription
JOIN renewal_history AS history
    ON history.product_name = current_subscription.product_name
ON CONFLICT (customer_id, product_id, subscription_start_date) DO UPDATE
SET licensed_seats = EXCLUDED.licensed_seats,
    subscription_end_date = EXCLUDED.subscription_end_date,
    subscription_status = EXCLUDED.subscription_status;

INSERT INTO intelligence_snapshots (
    id, customer_id, recommended_next_steps, industry_dynamics,
    company_news, ai_key_signal, metrics, generated_at
)
VALUES
    (
        '50000000-0000-0000-0000-000000000001',
        (SELECT id FROM customers WHERE name = 'ABC Bank'),
        '{
          "crossSell": [{"action": "Evaluate the Collaboration Tool", "priority": "medium", "reason": "ABC Bank subscribes to CRM and Analytics but not Collaboration.", "dueDate": null}],
          "upsell": [{"action": "Review licensed seat capacity", "priority": "medium", "reason": "The account currently holds 800 seats across two products.", "dueDate": null}],
          "renewal": [{"action": "Prepare a quantified subscription value review", "priority": "medium", "reason": "The subscriptions are active, but the next renewal is outside the highest-urgency window.", "dueDate": null}],
          "winback": [{"action": "Monitor inactive teams before outreach", "priority": "low", "reason": "No current product is canceled.", "dueDate": null}]
        }'::JSONB,
        '[{
          "headline": "Financial institutions are prioritizing workflow automation",
          "summary": "Banks continue investing in integrated data and automation capabilities.",
          "impact": "Position cross-product automation and analytics outcomes."
        }, {
          "headline": "Banks are strengthening data governance and AI oversight",
          "summary": "Financial institutions are tightening controls around customer data, analytics, and automated decisions.",
          "impact": "Connect CRM and analytics value to governed workflows, auditability, and risk reduction."
        }]'::JSONB,
        '[{
          "headline": "ABC Bank launches a digital onboarding modernization initiative",
          "summary": "Synthetic demo scenario — not real company news. This fictional program would simplify customer onboarding and connect service workflows.",
          "sourceName": "DealBrief Synthetic Scenario",
          "sourceUrl": null,
          "publishedDate": "2026-07-18",
          "sourceType": "synthetic",
          "isMock": true
        }, {
          "headline": "ABC Bank expands its enterprise data governance program",
          "summary": "Synthetic demo scenario — not real company news. This fictional announcement highlights stronger analytics controls, audit processes, and shared data standards.",
          "sourceName": "DealBrief Synthetic Scenario",
          "sourceUrl": null,
          "publishedDate": "2026-06-24",
          "sourceType": "synthetic",
          "isMock": true
        }]'::JSONB,
        'ABC Bank has 800 licensed seats across two active product subscriptions.',
        '{
          "accountHealthScore": 74,
          "totalLicensedSeats": 800,
          "activeSubscriptions": 2,
          "riskReasons": ["CRM subscription renews first"]
        }'::JSONB,
        NOW()
    ),
    (
        '50000000-0000-0000-0000-000000000002',
        (SELECT id FROM customers WHERE name = 'Northstar Retail'),
        '{
          "crossSell": [{"action": "Hold cross-sell outreach and focus on portfolio value", "priority": "low", "reason": "Northstar already holds all three active products, so no never-purchased product gap exists.", "dueDate": null}],
          "upsell": [{"action": "Review capacity for expanding retail teams", "priority": "high", "reason": "The account has 2,157 licensed seats across its portfolio.", "dueDate": null}],
          "renewal": [{"action": "Document subscription value across stores", "priority": "high", "reason": "The large active portfolio and upcoming renewal window make value documentation strategically important.", "dueDate": null}],
          "winback": [{"action": "Monitor product coverage before targeted outreach", "priority": "low", "reason": "No subscription is currently canceled.", "dueDate": null}]
        }'::JSONB,
        '[{
          "headline": "Retailers are unifying store operations and customer data",
          "summary": "Retail teams are consolidating collaboration, forecasting, and customer workflows.",
          "impact": "Frame the platform as a connected operating layer across locations."
        }, {
          "headline": "Margin pressure is increasing demand for forecast accuracy",
          "summary": "Retailers are prioritizing inventory visibility and faster decisions as operating costs remain under pressure.",
          "impact": "Use Northstar''s analytics footprint to lead a forecasting and capacity optimization discussion."
        }]'::JSONB,
        '[{
          "headline": "Northstar Retail pilots a unified inventory command center",
          "summary": "Synthetic demo scenario — not real company news. This fictional pilot connects store activity, inventory signals, and forecasting through shared dashboards.",
          "sourceName": "DealBrief Synthetic Scenario",
          "sourceUrl": null,
          "publishedDate": "2026-07-22",
          "sourceType": "synthetic",
          "isMock": true
        }, {
          "headline": "Northstar Retail expands its store collaboration rollout",
          "summary": "Synthetic demo scenario — not real company news. This fictional update describes standardized workflows expanding across regional store teams.",
          "sourceName": "DealBrief Synthetic Scenario",
          "sourceUrl": null,
          "publishedDate": "2026-06-30",
          "sourceType": "synthetic",
          "isMock": true
        }]'::JSONB,
        'Northstar has the largest seat footprint with 2,157 seats across three active subscriptions.',
        '{
          "accountHealthScore": 88,
          "totalLicensedSeats": 2157,
          "activeSubscriptions": 3,
          "riskReasons": ["CRM subscription renews before the other products"]
        }'::JSONB,
        NOW()
    ),
    (
        '50000000-0000-0000-0000-000000000003',
        (SELECT id FROM customers WHERE name = 'GreenHealth Group'),
        '{
          "crossSell": [{"action": "Validate CRM pilot value before introducing another product", "priority": "low", "reason": "Product gaps exist, but the small pilot footprint and distant renewal reduce immediate urgency.", "dueDate": null}],
          "upsell": [{"action": "Review CRM seat expansion after the pilot", "priority": "low", "reason": "The current CRM subscription contains 200 licensed seats.", "dueDate": null}],
          "renewal": [{"action": "Create a focused CRM pilot success plan", "priority": "low", "reason": "The single 200-seat subscription is active and remains outside the immediate renewal window.", "dueDate": null}],
          "winback": [{"action": "Monitor the pilot for disengagement", "priority": "low", "reason": "No product is currently expired or canceled, so there is no eligible winback motion.", "dueDate": null}]
        }'::JSONB,
        '[{
          "headline": "Healthcare organizations are emphasizing measurable technology adoption",
          "summary": "Providers are prioritizing workflow tools that demonstrate operational impact and user adoption.",
          "impact": "Use pilot milestones and department-level outcomes to support expansion."
        }, {
          "headline": "Healthcare data privacy remains central to digital workflow decisions",
          "summary": "Providers continue evaluating new platforms against security, access control, and patient-data requirements.",
          "impact": "Include governance and controlled CRM access in GreenHealth''s pilot success criteria."
        }]'::JSONB,
        '[{
          "headline": "GreenHealth Group begins a CRM-enabled patient services pilot",
          "summary": "Synthetic demo scenario — not real company news. This fictional pilot connects service requests and follow-up workflows for a limited group of care teams.",
          "sourceName": "DealBrief Synthetic Scenario",
          "sourceUrl": null,
          "publishedDate": "2026-07-15",
          "sourceType": "synthetic",
          "isMock": true
        }, {
          "headline": "GreenHealth Group forms a digital workflow governance council",
          "summary": "Synthetic demo scenario — not real company news. This fictional council would review access controls, adoption measures, and operational outcomes for new platforms.",
          "sourceName": "DealBrief Synthetic Scenario",
          "sourceUrl": null,
          "publishedDate": "2026-06-19",
          "sourceType": "synthetic",
          "isMock": true
        }]'::JSONB,
        'GreenHealth has 200 licensed CRM seats while remaining in pilot status.',
        '{
          "accountHealthScore": 64,
          "totalLicensedSeats": 200,
          "activeSubscriptions": 1,
          "riskReasons": ["Customer remains in pilot status"]
        }'::JSONB,
        NOW()
    ),
    (
        '50000000-0000-0000-0000-000000000004',
        (SELECT id FROM customers WHERE name = 'Summit Manufacturing'),
        '{
          "crossSell": [{"action": "Evaluate collaboration approvals", "priority": "medium", "reason": "Summit subscribes to CRM and Analytics but not Collaboration.", "dueDate": null}],
          "upsell": [{"action": "Assess additional seat capacity for operations teams", "priority": "medium", "reason": "The portfolio contains 550 licensed seats.", "dueDate": null}],
          "renewal": [{"action": "Quantify cross-product workflow value", "priority": "medium", "reason": "Both subscriptions are active.", "dueDate": null}],
          "winback": [{"action": "Monitor for future product contraction", "priority": "low", "reason": "No current subscription is canceled.", "dueDate": null}]
        }'::JSONB,
        '[{
          "headline": "Manufacturers are expanding connected operational analytics",
          "summary": "Manufacturing teams continue linking production data with automated decision workflows.",
          "impact": "Lead with integrated reporting, approvals, and frontline collaboration."
        }, {
          "headline": "Supply-chain resilience is driving predictive planning investments",
          "summary": "Manufacturers are using shared operational data to anticipate disruptions and adjust capacity sooner.",
          "impact": "Position Summit''s analytics subscription around proactive planning and cross-team response."
        }]'::JSONB,
        '[{
          "headline": "Summit Manufacturing opens a connected operations program",
          "summary": "Synthetic demo scenario — not real company news. This fictional program links production reporting with faster planning and exception-management workflows.",
          "sourceName": "DealBrief Synthetic Scenario",
          "sourceUrl": null,
          "publishedDate": "2026-07-25",
          "sourceType": "synthetic",
          "isMock": true
        }, {
          "headline": "Summit Manufacturing expands its predictive planning initiative",
          "summary": "Synthetic demo scenario — not real company news. This fictional initiative uses shared operational analytics to identify capacity risks earlier.",
          "sourceName": "DealBrief Synthetic Scenario",
          "sourceUrl": null,
          "publishedDate": "2026-06-27",
          "sourceType": "synthetic",
          "isMock": true
        }]'::JSONB,
        'Summit maintains 550 licensed seats across two active product subscriptions.',
        '{
          "accountHealthScore": 84,
          "totalLicensedSeats": 550,
          "activeSubscriptions": 2,
          "riskReasons": ["CRM subscription renews first"]
        }'::JSONB,
        NOW()
    ),
    (
        '50000000-0000-0000-0000-000000000005',
        (SELECT id FROM customers WHERE name = 'BrightPath Education'),
        '{
          "crossSell": [{"action": "Evaluate CRM for student services", "priority": "medium", "reason": "BrightPath subscribes to Collaboration and Analytics but not CRM.", "dueDate": null}],
          "upsell": [{"action": "Review seat capacity before the next academic term", "priority": "medium", "reason": "BrightPath holds 925 licensed seats.", "dueDate": null}],
          "renewal": [{"action": "Build a value review around staff coordination", "priority": "medium", "reason": "Both subscriptions are active.", "dueDate": null}],
          "winback": [{"action": "Monitor for future product contraction", "priority": "low", "reason": "No subscription is currently canceled.", "dueDate": null}]
        }'::JSONB,
        '[{
          "headline": "Education organizations are modernizing student and staff workflows",
          "summary": "Institutions are investing in connected collaboration, engagement, and reporting tools.",
          "impact": "Tie product adoption to coordinated student-service outcomes."
        }, {
          "headline": "Education technology budgets increasingly require measurable outcomes",
          "summary": "Institutions are scrutinizing platform consolidation, staff productivity, and student-service impact.",
          "impact": "Build BrightPath''s renewal story around coordinated workflows and quantifiable service improvements."
        }]'::JSONB,
        '[{
          "headline": "BrightPath Education launches a coordinated student support program",
          "summary": "Synthetic demo scenario — not real company news. This fictional program gives staff shared workflows for tracking service requests and follow-up actions.",
          "sourceName": "DealBrief Synthetic Scenario",
          "sourceUrl": null,
          "publishedDate": "2026-07-20",
          "sourceType": "synthetic",
          "isMock": true
        }, {
          "headline": "BrightPath Education expands analytics for retention planning",
          "summary": "Synthetic demo scenario — not real company news. This fictional update describes dashboards intended to help teams coordinate earlier student interventions.",
          "sourceName": "DealBrief Synthetic Scenario",
          "sourceUrl": null,
          "publishedDate": "2026-06-21",
          "sourceType": "synthetic",
          "isMock": true
        }]'::JSONB,
        'BrightPath has 925 licensed seats across two active subscriptions.',
        '{
          "accountHealthScore": 78,
          "totalLicensedSeats": 925,
          "activeSubscriptions": 2,
          "riskReasons": ["Analytics subscription renews before the other products"]
        }'::JSONB,
        NOW()
    )
ON CONFLICT (id) DO UPDATE
SET customer_id = EXCLUDED.customer_id,
    recommended_next_steps = EXCLUDED.recommended_next_steps,
    industry_dynamics = EXCLUDED.industry_dynamics,
    company_news = EXCLUDED.company_news,
    ai_key_signal = EXCLUDED.ai_key_signal,
    metrics = EXCLUDED.metrics,
    generated_at = EXCLUDED.generated_at;

COMMIT;
