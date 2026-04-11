from sqlalchemy.orm import Session
from uuid import UUID
from database.models.catalog.variants import Sku


def create_sku(db: Session, data: dict) -> Sku:
    sku = Sku(**data)
    db.add(sku)
    db.commit()
    db.refresh(sku)
    return sku

def update_sku(db: Session, sku_id: UUID, data: dict):
    sku = db.query(Sku).filter(Sku.id == sku_id).first()

    if not sku:
        return None

    for key, value in data.items():
        setattr(sku, key, value)

    db.commit()
    db.refresh(sku)
    return sku

def get_sku(db: Session, sku_id: UUID):
    return db.query(Sku).filter(Sku.id == sku_id).first()


def get_skus_by_product(db: Session, product_id: UUID):
    return db.query(Sku).filter(Sku.product_id == product_id).all()