from decimal import Decimal


def iso(value):
    return value.isoformat() if value else None


def number(value):
    return float(value) if isinstance(value, Decimal) else value


def serialize_customer(customer):
    return {
        "id": str(customer.id),
        "name": customer.name,
        "industry": customer.industry,
        "accountOwner": None
        if not customer.account_owner
        else {
            "id": str(customer.account_owner.id),
            "name": customer.account_owner.name,
        },
        "salesforceAccountId": customer.salesforce_account_id,
        "opportunityStage": customer.opportunity_stage,
        "renewalDate": iso(customer.renewal_date),
        "status": customer.status,
    }


def serialize_usage(usage):
    return {
        "id": str(usage.id),
        "customerId": str(usage.customer_id),
        "customerName": usage.customer.name if usage.customer else None,
        "productId": str(usage.product_id),
        "productName": usage.product.name,
        "snapshotDate": iso(usage.snapshot_date),
        "activeUsers": usage.active_users,
        "licensedSeats": usage.licensed_seats,
        "licenseUtilization": number(usage.license_utilization),
        "usageGrowth": number(usage.usage_growth),
        "featureAdoption": usage.feature_adoption,
    }


def serialize_intelligence(snapshot):
    if not snapshot:
        return None
    actions = snapshot.next_best_actions or []
    return {
        "id": str(snapshot.id),
        "snapshotDate": iso(snapshot.snapshot_date),
        "aiKeySignal": snapshot.ai_key_signal,
        "nextBestActions": actions,
        "metrics": snapshot.metrics,
        "periodStart": iso(snapshot.period_start),
        "periodEnd": iso(snapshot.period_end),
        "sourceDataThrough": iso(snapshot.source_data_through),
        "generationStatus": snapshot.generation_status,
        "model": snapshot.model,
        "generatedAt": iso(snapshot.generated_at),
    }


def serialize_engagement(engagement, include_content=False):
    result = {
        "id": str(engagement.id),
        "customerId": str(engagement.customer_id),
        "customerName": engagement.customer.name,
        "productId": str(engagement.product_id) if engagement.product_id else None,
        "product": engagement.product.name if engagement.product else None,
        "meetingType": engagement.meeting_type,
        "deliverableType": engagement.deliverable_type,
        "title": engagement.title,
        "summary": engagement.summary,
        "meetingSummary": engagement.summary,
        "status": engagement.status,
        "generatedAt": iso(engagement.generated_at),
        "date": iso(engagement.generated_at),
        "generatedBy": engagement.author.name if engagement.author else "DealBrief AI",
    }
    if include_content:
        result.update(
            {
                "notes": engagement.notes,
                "content": engagement.content,
                "inputSnapshot": engagement.input_snapshot,
                "model": engagement.model,
                "promptVersion": engagement.prompt_version,
            }
        )
    return result


def serialize_import_job(job):
    return {
        "id": str(job.id),
        "importType": job.import_type,
        "filename": job.filename,
        "status": job.status,
        "totalRows": job.total_rows,
        "insertedRows": job.inserted_rows,
        "updatedRows": job.updated_rows,
        "failedRows": job.failed_rows,
        "errorDetails": job.error_details or [],
        "uploadedBy": None
        if not job.uploader
        else {
            "id": str(job.uploader.id),
            "name": job.uploader.name,
        },
        "createdAt": iso(job.created_at),
        "completedAt": iso(job.completed_at),
    }
