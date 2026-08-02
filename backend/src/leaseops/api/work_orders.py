from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from leaseops.api.schemas import (
    WorkOrderCreate,
    WorkOrderListResponse,
    WorkOrderResponse,
    WorkOrderUpdate,
)
from leaseops.db import work_orders as repo
from leaseops.db.session import get_session
from leaseops.models.enums import WorkOrderStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/work-orders", tags=["work-orders"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "",
    response_model=WorkOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_work_order(
    payload: WorkOrderCreate,
    session: SessionDep,
) -> WorkOrderResponse:
    work_order = await repo.create_work_order(session, payload)
    logger.info(
        "work_order_created",
        extra={
            "work_order_id": str(work_order.id),
            "tenant_id": str(work_order.tenant_id),
            "status": work_order.status,
        },
    )
    return WorkOrderResponse.model_validate(work_order)


@router.get("", response_model=WorkOrderListResponse)
async def list_work_orders(
    session: SessionDep,
    status_filter: Annotated[WorkOrderStatus | None, Query(alias="status")] = None,
) -> WorkOrderListResponse:
    items = await repo.list_work_orders(session, status=status_filter)
    return WorkOrderListResponse(
        items=[WorkOrderResponse.model_validate(item) for item in items]
    )


@router.get("/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(
    work_order_id: UUID,
    session: SessionDep,
) -> WorkOrderResponse:
    work_order = await repo.get_work_order(session, work_order_id)
    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="work order not found"
        )
    return WorkOrderResponse.model_validate(work_order)


@router.patch("/{work_order_id}", response_model=WorkOrderResponse)
async def update_work_order(
    work_order_id: UUID,
    payload: WorkOrderUpdate,
    session: SessionDep,
) -> WorkOrderResponse:
    work_order = await repo.get_work_order(session, work_order_id)
    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="work order not found"
        )
    updated = await repo.update_work_order(session, work_order, payload)
    logger.info(
        "work_order_updated",
        extra={
            "work_order_id": str(updated.id),
            "status": updated.status,
        },
    )
    return WorkOrderResponse.model_validate(updated)


@router.delete("/{work_order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_order(
    work_order_id: UUID,
    session: SessionDep,
) -> None:
    work_order = await repo.get_work_order(session, work_order_id)
    if work_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="work order not found"
        )
    await repo.delete_work_order(session, work_order)
    logger.info(
        "work_order_deleted",
        extra={"work_order_id": str(work_order_id)},
    )
