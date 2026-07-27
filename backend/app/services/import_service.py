import json
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from sqlalchemy import func, or_

from ..errors import ApiError
from ..extensions import db
from ..models import Customer, ImportJob, Product, UsageSnapshot, User


def _required_text(row, keys, label):
    value = _value(row, keys)
    if value is None or not str(value).strip():
        raise ValueError(f"{label} is required")
    return str(value).strip()


def _value(row, keys, default=None):
    normalized = {
        str(key).strip().lower().replace("_", "").replace(" ", ""): value
        for key, value in row.items()
    }
    for key in keys:
        candidate = normalized.get(key.lower().replace("_", "").replace(" ", ""))
        if candidate not in (None, ""):
            return candidate
    return default


def _date(value, label, default=None):
    if value in (None, ""):
        if default is not None:
            return default
        raise ValueError(f"{label} is required")
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as error:
        raise ValueError(f"{label} must use YYYY-MM-DD") from error


def _integer(value, label, default=None):
    if value in (None, ""):
        if default is not None:
            return default
        raise ValueError(f"{label} is required")
    try:
        return int(str(value).replace(",", "").strip())
    except ValueError as error:
        raise ValueError(f"{label} must be an integer") from error


def _decimal(value, label, default=None):
    if value in (None, ""):
        return default
    try:
        return Decimal(str(value).replace("%", "").replace("+", "").strip())
    except InvalidOperation as error:
        raise ValueError(f"{label} must be numeric") from error


def _feature_adoption(value):
    if value in (None, ""):
        return {}
    if isinstance(value, dict):
        return value
    text = str(value).strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    result = {}
    for segment in text.replace(";", ",").split(","):
        if not segment.strip():
            continue
        if ":" in segment:
            key, raw_value = segment.split(":", 1)
        else:
            parts = segment.strip().rsplit(" ", 1)
            if len(parts) != 2:
                result[segment.strip()] = None
                continue
            key, raw_value = parts
        number = _decimal(raw_value, "feature adoption", default=None)
        result[key.strip()] = float(number) if number is not None else None
    return result


def _uploaded_by(value):
    if not value:
        return None
    try:
        user_id = UUID(str(value))
    except (TypeError, ValueError) as error:
        raise ApiError("VALIDATION_ERROR", "uploadedBy must be a valid UUID.", 422) from error
    if not db.session.get(User, user_id):
        raise ApiError("USER_NOT_FOUND", "The uploadedBy user does not exist.", 404)
    return user_id


def _validate_payload(payload):
    if not isinstance(payload, dict):
        raise ApiError("VALIDATION_ERROR", "A JSON request body is required.", 422)
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ApiError("VALIDATION_ERROR", "rows must be a non-empty array.", 422)
    if len(rows) > 5000:
        raise ApiError("VALIDATION_ERROR", "A single import supports at most 5000 rows.", 422)
    if any(not isinstance(row, dict) for row in rows):
        raise ApiError("VALIDATION_ERROR", "Every item in rows must be an object.", 422)
    filename = str(payload.get("filename") or "api-import.json").strip()
    if len(filename) > 255:
        raise ApiError("VALIDATION_ERROR", "filename must be 255 characters or fewer.", 422)
    return filename, rows, _uploaded_by(payload.get("uploadedBy"))


def _new_job(import_type, filename, rows, uploaded_by):
    job = ImportJob(
        uploaded_by=uploaded_by,
        import_type=import_type,
        filename=filename,
        status="processing",
        total_rows=len(rows),
        inserted_rows=0,
        updated_rows=0,
        failed_rows=0,
        error_details=[],
    )
    db.session.add(job)
    db.session.flush()
    return job


def _owner_id(row):
    reference = _value(row, ["accountOwnerId", "accountOwner", "owner"])
    if not reference:
        return None
    try:
        owner_uuid = UUID(str(reference))
    except (TypeError, ValueError):
        normalized = str(reference).strip().lower()
        owner = User.query.filter(
            or_(func.lower(User.name) == normalized, func.lower(User.email) == normalized)
        ).first()
    else:
        owner = db.session.get(User, owner_uuid)
    return owner.id if owner else None


def import_customers(payload):
    filename, rows, uploaded_by = _validate_payload(payload)
    job = _new_job("customers", filename, rows, uploaded_by)
    errors = []
    now = datetime.now(timezone.utc)

    for row_number, row in enumerate(rows, start=1):
        try:
            name = _required_text(row, ["name", "customerName", "customer"], "name")
            salesforce_id = _required_text(
                row,
                ["salesforceAccountId", "salesforceId", "accountId"],
                "salesforceAccountId",
            )
            customer = Customer.query.filter_by(salesforce_account_id=salesforce_id).first()
            is_insert = customer is None
            if is_insert:
                customer = Customer(
                    id=uuid4(),
                    created_at=now,
                    updated_at=now,
                    status="active",
                )
                db.session.add(customer)

            status = str(_value(row, ["status"], customer.status or "active")).strip().lower()
            if status not in {"active", "pilot", "inactive"}:
                raise ValueError("status must be active, pilot, or inactive")

            renewal_value = _value(row, ["renewalDate"])
            customer.name = name
            customer.industry = _value(row, ["industry"])
            customer.account_owner_id = _owner_id(row)
            customer.salesforce_account_id = salesforce_id
            customer.opportunity_stage = _value(row, ["opportunityStage", "stage"])
            customer.renewal_date = (
                _date(renewal_value, "renewalDate") if renewal_value not in (None, "") else None
            )
            customer.status = status
            customer.updated_at = now
            customer.deleted_at = None
            customer.source_import_job_id = job.id
            job.inserted_rows += int(is_insert)
            job.updated_rows += int(not is_insert)
        except ValueError as error:
            job.failed_rows += 1
            errors.append({"row": row_number, "message": str(error)})

    job.error_details = errors
    job.status = "completed" if not errors else ("failed" if job.failed_rows == len(rows) else "completed")
    job.completed_at = datetime.now(timezone.utc)
    db.session.commit()
    return job


def _find_customer(row):
    customer_id = _value(row, ["customerId"])
    if customer_id:
        try:
            customer = db.session.get(Customer, UUID(str(customer_id)))
        except (TypeError, ValueError) as error:
            raise ValueError("customerId must be a valid UUID") from error
    else:
        salesforce_id = _value(row, ["salesforceAccountId", "salesforceId", "accountId"])
        customer_name = _value(row, ["customerName", "customer"])
        customer = None
        if salesforce_id:
            customer = Customer.query.filter_by(salesforce_account_id=str(salesforce_id).strip()).first()
        if not customer and customer_name:
            customer = Customer.query.filter(
                func.lower(Customer.name) == str(customer_name).strip().lower()
            ).first()
    if not customer or customer.deleted_at is not None:
        raise ValueError("customer was not found")
    return customer


def _find_product(row):
    product_id = _value(row, ["productId"])
    if product_id:
        try:
            product = db.session.get(Product, UUID(str(product_id)))
        except (TypeError, ValueError) as error:
            raise ValueError("productId must be a valid UUID") from error
    else:
        product_name = _required_text(row, ["productName", "product"], "productName")
        product = Product.query.filter(
            func.lower(Product.name) == product_name.lower()
        ).first()
    if not product or product.status != "active":
        raise ValueError("active product was not found")
    return product


def import_usage(payload):
    filename, rows, uploaded_by = _validate_payload(payload)
    job = _new_job("usage", filename, rows, uploaded_by)
    errors = []

    for row_number, row in enumerate(rows, start=1):
        try:
            customer = _find_customer(row)
            product = _find_product(row)
            snapshot_date = _date(
                _value(row, ["snapshotDate", "lastUpdated"]),
                "snapshotDate",
                default=date.today(),
            )
            active_users = _integer(_value(row, ["activeUsers"]), "activeUsers", default=0)
            licensed_seats = _integer(
                _value(row, ["licensedSeats"]), "licensedSeats", default=None
            )
            if active_users < 0 or (licensed_seats is not None and licensed_seats < 0):
                raise ValueError("user and seat counts cannot be negative")

            utilization = _decimal(
                _value(row, ["licenseUtilization"]), "licenseUtilization", default=None
            )
            if utilization is None and licensed_seats:
                utilization = Decimal(active_users * 100) / Decimal(licensed_seats)
            growth = _decimal(_value(row, ["usageGrowth"]), "usageGrowth", default=None)

            usage = UsageSnapshot.query.filter_by(
                customer_id=customer.id,
                product_id=product.id,
                snapshot_date=snapshot_date,
            ).first()
            is_insert = usage is None
            if is_insert:
                usage = UsageSnapshot(
                    id=uuid4(),
                    customer_id=customer.id,
                    product_id=product.id,
                    snapshot_date=snapshot_date,
                )
                db.session.add(usage)

            usage.active_users = active_users
            usage.licensed_seats = licensed_seats
            usage.license_utilization = utilization
            usage.usage_growth = growth
            usage.feature_adoption = _feature_adoption(_value(row, ["featureAdoption"]))
            usage.import_job_id = job.id
            job.inserted_rows += int(is_insert)
            job.updated_rows += int(not is_insert)
        except ValueError as error:
            job.failed_rows += 1
            errors.append({"row": row_number, "message": str(error)})

    job.error_details = errors
    job.status = "completed" if not errors else ("failed" if job.failed_rows == len(rows) else "completed")
    job.completed_at = datetime.now(timezone.utc)
    db.session.commit()
    return job
