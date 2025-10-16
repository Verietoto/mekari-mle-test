from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


class FraudTransactionModel(BaseModel):
    id: Optional[int] = Field(None, description="Auto-incremented primary key")
    record_index: Optional[int] = Field(None, description="Index of the record")
    
    trans_date_trans_time: datetime = Field(..., description="Timestamp of the transaction")
    cc_num: int = Field(..., description="Credit card number (masked)")
    merchant: str = Field(..., description="Merchant name")
    category: str = Field(..., description="Merchant category")
    amt: float = Field(..., description="Transaction amount")
    first_name: str = Field(..., description="Customer's first name")
    last_name: str = Field(..., description="Customer's last name")
    gender: Optional[str] = Field(None, description="Customer gender: 'M' or 'F'")
    street: str = Field(..., description="Customer street address")
    city: str = Field(..., description="Customer city")
    state: str = Field(..., description="Customer state")
    zip: int = Field(..., description="Customer ZIP code")
    lat: Optional[float] = Field(None, description="Customer latitude")
    long_: Optional[float] = Field(None, alias="long", description="Customer longitude")
    city_pop: Optional[int] = Field(None, description="Population of customer's city")
    job: Optional[str] = Field(None, description="Customer occupation")
    dob: Optional[date] = Field(None, description="Customer date of birth")
    trans_num: str = Field(..., description="Transaction identifier")
    unix_time: int = Field(..., description="Timestamp in epoch seconds")
    merch_lat: Optional[float] = Field(None, description="Merchant latitude")
    merch_long: Optional[float] = Field(None, description="Merchant longitude")
    is_fraud: bool = Field(..., description="Indicates if the transaction is fraudulent (True or False not true or false) ")

    class Config:
        populate_by_name = True
