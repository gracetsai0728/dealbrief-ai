from sqlalchemy.dialects.postgresql import UUID

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()")
    )
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    role = db.Column(db.String(30), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.true())
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=db.func.now()
    )


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()")
    )
    name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100))
    status = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False)
    deleted_at = db.Column(db.DateTime(timezone=True))


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()")
    )
    name = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False)


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()")
    )
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customers.id"), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey("products.id"), nullable=False)
    subscription_start_date = db.Column(db.Date, nullable=False)
    subscription_end_date = db.Column(db.Date)
    subscription_status = db.Column(db.String(20), nullable=False, server_default="active")
    licensed_seats = db.Column(db.Integer)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, server_default=db.func.now()
    )

    product = db.relationship("Product")
    customer = db.relationship("Customer")


class IntelligenceSnapshot(db.Model):
    __tablename__ = "intelligence_snapshots"

    id = db.Column(
        UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()")
    )
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customers.id"), nullable=False)
    recommended_next_steps = db.Column(
        db.JSON, nullable=False, server_default=db.text("'{}'::jsonb")
    )
    industry_dynamics = db.Column(
        db.JSON, nullable=False, server_default=db.text("'[]'::jsonb")
    )
    company_news = db.Column(
        db.JSON, nullable=False, server_default=db.text("'[]'::jsonb")
    )
    ai_key_signal = db.Column(db.Text)
    metrics = db.Column(db.JSON, nullable=False)
    generated_at = db.Column(db.DateTime(timezone=True), nullable=False)

    customer = db.relationship("Customer")
