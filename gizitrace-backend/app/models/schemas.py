from pydantic import BaseModel

class FeedbackSubmit(BaseModel):
    school_id: str
    class_id: str
    response_full: int
    response_half: int
    response_reject: int

class DeliveryCreate(BaseModel):
    vendor_id: str
    school_id: str
    reported_portions: int
    menu_description: str

class DeliveryConfirm(BaseModel):
    delivery_id: str
    confirmed_by: str
