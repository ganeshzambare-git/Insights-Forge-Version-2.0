"""
Insight Forge V2 — Tenants Router.

Exposes REST CRUD endpoints governing Tenant partitions, restricted to Admin.
"""

from typing import Any
import uuid
from fastapi import APIRouter, Depends, Request, status

from app.core.roles import Role
from app.dependencies.auth import RequireRoles
from app.dependencies.services import get_tenant_service
from app.services.tenant import TenantService
from app.api.v1.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.utils.response import api_response
from app.services.exceptions import NotFoundError

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
    dependencies=[Depends(RequireRoles(Role.ADMIN))],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
    summary="Create Tenant",
    description="Establish a new institutional tenant partition.",
)
async def create_tenant(
    request: Request,
    payload: TenantCreate,
    service: TenantService = Depends(get_tenant_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")
    result = await service.create_tenant(
        slug=payload.tenant_slug, name=payload.tenant_name
    )

    data = TenantResponse.model_validate(result.data).model_dump()
    return api_response(
        success=True,
        message=result.message or "Tenant created successfully.",
        data=data,
        request_id=req_id,
    )


@router.get(
    "/{tenant_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Get Tenant",
    description="Retrieve a tenant by UUID primary key.",
)
async def get_tenant(
    request: Request,
    tenant_id: uuid.UUID,
    service: TenantService = Depends(get_tenant_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")
    tenant = await service.get_tenant(tenant_id)
    if not tenant:
        raise NotFoundError(
            f"Tenant with ID '{tenant_id}' not found.",
            error_code="tenant_not_found",
        )

    data = TenantResponse.model_validate(tenant).model_dump()
    return api_response(
        success=True,
        message="Tenant retrieved successfully.",
        data=data,
        request_id=req_id,
    )


@router.patch(
    "/{tenant_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Update Tenant",
    description="Partially update tenant parameters (name or slug).",
)
async def update_tenant(
    request: Request,
    tenant_id: uuid.UUID,
    payload: TenantUpdate,
    service: TenantService = Depends(get_tenant_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")
    result = await service.update_tenant(
        tenant_id=tenant_id, name=payload.tenant_name, slug=payload.tenant_slug
    )

    data = TenantResponse.model_validate(result.data).model_dump()
    return api_response(
        success=True,
        message=result.message or "Tenant updated successfully.",
        data=data,
        request_id=req_id,
    )


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Tenant",
    description="Remove a tenant partition.",
)
async def delete_tenant(
    tenant_id: uuid.UUID,
    service: TenantService = Depends(get_tenant_service),
) -> None:
    await service.delete_tenant(tenant_id)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="List Tenants",
    description="List all registered tenants.",
)
async def list_tenants(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    service: TenantService = Depends(get_tenant_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")
    tenants = await service.list_tenants(limit=limit, offset=offset)

    data = [TenantResponse.model_validate(t).model_dump() for t in tenants]
    meta = {
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(data),
        }
    }
    return api_response(
        success=True,
        message="Tenants listed successfully.",
        data=data,
        meta=meta,
        request_id=req_id,
    )


public_router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
)


@public_router.get(
    "/verify/{slug}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Verify Tenant Slug",
    description="Verify if a tenant exists by slug without authentication.",
)
async def verify_tenant(
    request: Request,
    slug: str,
    service: TenantService = Depends(get_tenant_service),
) -> dict[str, Any]:
    req_id = getattr(request.state, "request_id", "unknown-req-id")
    tenant = await service.get_tenant_by_slug(slug)
    if not tenant:
        raise NotFoundError(
            f"Tenant with active slug '{slug}' was not found.",
            error_code="tenant_not_found",
        )

    data = TenantResponse.model_validate(tenant).model_dump()
    return api_response(
        success=True,
        message="Tenant verified successfully.",
        data=data,
        request_id=req_id,
    )

