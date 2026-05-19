from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import database
from routers.auth import verify_token

router = APIRouter()


class TemplateCreate(BaseModel):
    name: str
    body: str


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    body: Optional[str] = None


@router.get("/")
async def list_templates(_payload: dict = Depends(verify_token)):
    """List all reply templates"""
    try:
        templates = database.get_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")


@router.post("/")
async def create_template(
    template: TemplateCreate,
    _payload: dict = Depends(verify_token)
):
    """Create a new reply template"""
    try:
        template_id = database.create_template(template.name, template.body)
        return {"id": template_id, "message": "Template created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")


@router.put("/{template_id}")
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    _payload: dict = Depends(verify_token)
):
    """Update an existing reply template"""
    try:
        existing = database.get_template(template_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Template not found")

        database.update_template(
            template_id,
            name=template_update.name,
            body=template_update.body
        )
        return {"message": "Template updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating template: {str(e)}")


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    _payload: dict = Depends(verify_token)
):
    """Delete a reply template"""
    try:
        existing = database.get_template(template_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Template not found")

        database.delete_template(template_id)
        return {"message": "Template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting template: {str(e)}")
