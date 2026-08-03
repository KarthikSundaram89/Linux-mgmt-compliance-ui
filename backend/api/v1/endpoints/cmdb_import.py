"""
CMDB Import Endpoints
=====================

Manage and trigger the EFS-based CMDB CSV import.
"""

from fastapi import APIRouter, Depends

from backend.authentication.dependencies import require_role
from backend.models.user import User
from backend.services.cmdb_import_service import CMDBImportService

router = APIRouter()


@router.get("/status")
async def get_import_status(
    current_user: User = Depends(require_role("admin", "operator")),
):
    """Get CMDB import configuration and validation status."""
    service = CMDBImportService()
    validation = await service.validate_configuration()
    return validation


@router.post("/trigger", status_code=202)
async def trigger_import(
    current_user: User = Depends(require_role("admin")),
):
    """Manually trigger a CMDB CSV import."""
    service = CMDBImportService()
    result = await service.run_import()
    return result.to_dict()


@router.get("/config")
async def get_import_config(
    current_user: User = Depends(require_role("admin")),
):
    """Get current CMDB import configuration."""
    from backend.settings.config import get_settings
    s = get_settings()
    return {
        "enabled": s.cmdb_import_enabled,
        "file_path": s.cmdb_import_path,
        "schedule": f"{s.cmdb_import_schedule_hour:02d}:{s.cmdb_import_schedule_minute:02d} UTC",
        "csv_delimiter": s.cmdb_csv_delimiter,
        "csv_encoding": s.cmdb_csv_encoding,
        "csv_has_header": s.cmdb_csv_has_header,
        "column_mapping": {
            "region": s.cmdb_col_region,
            "account_name": s.cmdb_col_account_name,
            "instance_id": s.cmdb_col_instance_id,
            "instance_ip": s.cmdb_col_instance_ip,
            "name": s.cmdb_col_name,
            "app_name": s.cmdb_col_app_name,
            "pdo": s.cmdb_col_pdo,
        },
        "default_credential_profile": s.cmdb_default_credential_profile,
        "default_ssh_port": s.cmdb_default_ssh_port,
    }
