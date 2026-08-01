from sqlalchemy.dialects.postgresql import UUID

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    role = db.Column(db.String(30), nullable=False)


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100))
    account_owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"))
    salesforce_account_id = db.Column(db.String(100), unique=True)
    opportunity_stage = db.Column(db.String(100))
    renewal_date = db.Column(db.Date)
    status = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False)
    deleted_at = db.Column(db.DateTime(timezone=True))
    source_import_job_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("import_jobs.id", use_alter=True)
    )

    account_owner = db.relationship("User")


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False)


class UsageSnapshot(db.Model):
    __tablename__ = "usage_snapshots"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customers.id"), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey("products.id"), nullable=False)
    snapshot_date = db.Column(db.Date, nullable=False)
    active_users = db.Column(db.Integer, nullable=False)
    licensed_seats = db.Column(db.Integer)
    license_utilization = db.Column(db.Numeric(5, 2))
    usage_growth = db.Column(db.Numeric(7, 2))
    feature_adoption = db.Column(db.JSON, nullable=False)
    import_job_id = db.Column(UUID(as_uuid=True), db.ForeignKey("import_jobs.id"))
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=db.func.now()
    )

    product = db.relationship("Product")
    customer = db.relationship("Customer")


class Engagement(db.Model):
    __tablename__ = "engagements"

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customers.id"), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey("products.id"))
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"))
    engagement_type = db.Column(db.String(30), nullable=False)
    meeting_type = db.Column(db.String(30))
    deliverable_type = db.Column(db.String(30))
    occurred_at = db.Column(db.DateTime(timezone=True), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text)
    notes = db.Column(db.Text)
    content = db.Column(db.JSON, nullable=False)
    input_snapshot = db.Column(db.JSON, nullable=False)
    model = db.Column(db.String(100))
    prompt_version = db.Column(db.String(50))
    status = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    generated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    customer = db.relationship("Customer")
    product = db.relationship("Product")
    author = db.relationship("User")


class IntelligenceSnapshot(db.Model):
    __tablename__ = "intelligence_snapshots"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customers.id"), nullable=False)
    snapshot_date = db.Column(db.Date, nullable=False)
    next_best_actions = db.Column(db.JSON, nullable=False, server_default=db.text("'[]'::jsonb"))
    ai_key_signal = db.Column(db.Text)
    last_interaction_at = db.Column(db.DateTime(timezone=True))
    metrics = db.Column(db.JSON, nullable=False)
    period_start = db.Column(db.DateTime(timezone=True))
    period_end = db.Column(db.DateTime(timezone=True))
    source_data_through = db.Column(db.DateTime(timezone=True))
    generation_status = db.Column(db.String(30), nullable=False, server_default="completed")
    model = db.Column(db.String(100))
    prompt_version = db.Column(db.String(50))
    generated_at = db.Column(db.DateTime(timezone=True), nullable=False)

    customer = db.relationship("Customer")


class ImportJob(db.Model):
    __tablename__ = "import_jobs"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()")
    )
    uploaded_by = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"))
    import_type = db.Column(db.String(30), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    total_rows = db.Column(db.Integer, nullable=False, server_default="0")
    inserted_rows = db.Column(db.Integer, nullable=False, server_default="0")
    updated_rows = db.Column(db.Integer, nullable=False, server_default="0")
    failed_rows = db.Column(db.Integer, nullable=False, server_default="0")
    error_details = db.Column(db.JSON, nullable=False, server_default=db.text("'[]'::jsonb"))
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=db.func.now()
    )
    completed_at = db.Column(db.DateTime(timezone=True))

    uploader = db.relationship("User")
