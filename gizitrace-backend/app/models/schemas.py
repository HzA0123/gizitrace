from pydantic import BaseModel
from typing import Optional, List

class FeedbackSubmit(BaseModel):
    school_id: str
    class_id: str
    delivery_id: str
    response: str # e.g., 'full', 'half', 'reject'

class DeliveryCreate(BaseModel):
    vendor_id: str
    school_id: str
    menu_description: str
    reported_portions: int
