from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item
from app.schemas import ItemCreate, ItemUpdate, ItemResponse

router = APIRouter(prefix="/items", tags=["Items"])


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, summary="Create Item")
def create_item(item_in: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(title=item_in.title, description=item_in.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/", response_model=List[ItemResponse], summary="List all Items")
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Item).offset(skip).limit(limit).all()


@router.get("/{item_id}", response_model=ItemResponse, summary="Get Item by ID")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=ItemResponse, summary="Update Item")
def update_item(item_id: int, item_in: ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item_in.title is not None:
        item.title = item_in.title
    if item_in.description is not None:
        item.description = item_in.description

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Item")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return None
