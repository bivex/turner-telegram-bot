from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import database
from routers.auth import verify_token

router = APIRouter()

DEFAULT_PAGE_LIMIT = 20


class CustomerUpdate(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
async def list_customers(
    page: int = 1,
    limit: int = DEFAULT_PAGE_LIMIT,
    _payload: dict = Depends(verify_token)
):
    """Paginated customer list"""
    try:
        offset = (page - 1) * limit
        customers = database.get_all_customers(limit, offset)
        total = database.get_customers_count()
        return {"customers": customers, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching customers: {str(e)}")


@router.get("/{user_id}")
async def get_customer_detail(
    user_id: int,
    _payload: dict = Depends(verify_token)
):
    """Customer detail with their orders"""
    try:
        customer = database.get_customer(user_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        orders = database.get_user_orders(user_id)
        return {"customer": customer, "orders": orders}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching customer: {str(e)}")


@router.put("/{user_id}")
async def update_customer(
    user_id: int,
    customer_update: CustomerUpdate,
    _payload: dict = Depends(verify_token)
):
    """Update customer profile (phone, email, notes)"""
    try:
        customer = database.get_customer(user_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        database.update_customer_profile(
            user_id,
            phone=customer_update.phone,
            email=customer_update.email,
            notes=customer_update.notes
        )
        database.recalculate_customer_stats(user_id)

        updated = database.get_customer(user_id)
        return {"customer": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating customer: {str(e)}")
