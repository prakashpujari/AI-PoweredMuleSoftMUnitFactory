"""Seed demo data for development/demo environments."""
import asyncio
import uuid
from app.database import AsyncSessionFactory, create_tables
from app.models.application import Application, ApiType, DeploymentTarget, ApplicationStatus
from app.models.flow import Flow, FlowType
from app.models.test_run import TestRun, RunStatus


DEMO_APPS = [
    {"name": "order-api", "api_type": ApiType.PROCESS, "business_unit": "Commerce", "domain": "Orders", "runtime": "4.6.0"},
    {"name": "customer-exp-api", "api_type": ApiType.EXPERIENCE, "business_unit": "CRM", "domain": "Customer", "runtime": "4.6.0"},
    {"name": "inventory-sys-api", "api_type": ApiType.SYSTEM, "business_unit": "Supply Chain", "domain": "Inventory", "runtime": "4.4.0"},
    {"name": "payment-process-api", "api_type": ApiType.PROCESS, "business_unit": "Finance", "domain": "Payments", "runtime": "4.6.0"},
    {"name": "product-catalog-api", "api_type": ApiType.EXPERIENCE, "business_unit": "Commerce", "domain": "Products", "runtime": "4.7.0"},
    {"name": "salesforce-sys-api", "api_type": ApiType.SYSTEM, "business_unit": "CRM", "domain": "Salesforce", "runtime": "4.6.0"},
    {"name": "notification-api", "api_type": ApiType.PROCESS, "business_unit": "Platform", "domain": "Notifications", "runtime": "4.6.0"},
    {"name": "reporting-exp-api", "api_type": ApiType.EXPERIENCE, "business_unit": "Analytics", "domain": "Reports", "runtime": "4.5.0"},
]


async def seed():
    await create_tables()
    async with AsyncSessionFactory() as session:
        for app_data in DEMO_APPS:
            app = Application(
                name=app_data["name"],
                artifact_id=app_data["name"],
                version="1.0.0",
                mule_runtime_version=app_data["runtime"],
                business_unit=app_data["business_unit"],
                domain=app_data["domain"],
                environment="development",
                api_type=app_data["api_type"],
                deployment_target=DeploymentTarget.CLOUDHUB,
                status=ApplicationStatus.TESTED,
                flows_count=15,
                connectors=["http", "database"],
                coverage_score=94.5,
                security_score=97.0,
                performance_score=95.0,
                quality_score=95.5,
                production_readiness_score=96.0,
                migration_readiness_score=75.0,
                risk_score=12.0,
            )
            session.add(app)

        await session.commit()
        print(f"Seeded {len(DEMO_APPS)} demo applications")


if __name__ == "__main__":
    asyncio.run(seed())
