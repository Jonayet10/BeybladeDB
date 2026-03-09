from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class AddToCollectionRequest(BaseModel):
    username: str
    beyblade_id: str
    bey_condition: str


class DeleteFromCollectionRequest(BaseModel):
    username: str
    user_beyblade_id: int

class UpdateCollectionConditionRequest(BaseModel):
    username: str
    user_beyblade_id: int
    bey_condition: str