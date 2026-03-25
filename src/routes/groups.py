from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from servises.groups.repository import GroupRepository
from servises.request.validate_data import ValidateData

router = APIRouter(tags=["groups"])


def parse_data(dat: str, reference_sale: str):
    items = dat.strip("|").split("|")
    parsed_items = []
    for item in items:
        parts = item.split(",")
        parsed_items.append(
            {
                "category_id": int(parts[0]),
                "google_id": parts[1] if len(parts) > 1 else None,
                "google_id_refer": parts[2] if len(parts) > 2 else None,
                "reference_code": reference_sale,
            }
        )
    return parsed_items


@router.post("/create-group", status_code=201)
def create_group(
    data: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    ValidateData.validate_request_data(
        required_fields=["group_email", "group_name", "group_description"],
        data=data,
    )
    group_repo = GroupRepository(
        group_email=data["group_email"],
        group_name=data["group_name"],
        group_description=data["group_description"],
    )
    result = group_repo.crear_grupo()
    if result:
        return result
    raise HTTPException(status_code=400, detail="Error al crear el grupo")


@router.post("/add-member")
def add_member(
    data: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    ValidateData.validate_request_data(required_fields=["extra1"], data=data)
    cart_data = parse_data(data.get("extra1"), "kkkkkkkkkkkk")
    response = {"error": "No se proporcionaron datos"}
    if isinstance(cart_data, list):
        for item in cart_data:
            response = GroupRepository.process_member_addition("agregar_miembro_grupo", data=item)
    return response


@router.post("/add-member-time")
def add_member_time(
    data: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    ValidateData.validate_request_data(required_fields=["extra1"], data=data)
    cart_data = parse_data(data.get("extra1"), "kkkkkkkkkkkk")
    response = {"error": "No se proporcionaron datos"}
    if isinstance(cart_data, list):
        for item in cart_data:
            response = GroupRepository.process_member_addition(
                "agregar_miembro_grupo_time", data=item
            )
    return response


@router.delete("/remove-member")
def remove_member(
    data: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    ValidateData.validate_request_data(
        required_fields=["group_email", "member_email"],
        data=data,
    )
    group_repo = GroupRepository(
        group_email=data["group_email"],
        member_email=data["member_email"],
    )
    result = group_repo.eliminar_miembro_grupo()
    if result:
        return {
            "message": f"Miembro {data['member_email']} eliminado del grupo {data['group_email']}"
        }
    raise HTTPException(status_code=400, detail="Error al eliminar el miembro del grupo")
