from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class NoiseRequestParams(BaseModel):
    """
    Model for data in API request made for getting noise measurements.
    """

    granularity: Literal["raw", "hourly", "life-time"] = "raw"
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    page: Optional[int] = Field(default=None, ge=0)


class Location(BaseModel):
    """
    Single location model.
    """

    id: str
    label: str
    latitude: float
    longitude: float
    radius: int
    active: bool

    @field_validator("id", mode="before")
    def id_to_str(cls, value):
        return str(value)


class LocationsData(BaseModel):
    """
    Locations data model.
    """

    locations: List[Location]


class Noise(BaseModel):
    """
    Noise measurement value.
    """

    min: float
    max: float
    mean: float


class NoiseTimed(Noise):
    """
    Noise measurement value with timestamp.
    """

    timestamp: datetime


class LocationNoiseData(BaseModel):
    """
    Location noise data.
    """

    measurements: List[Noise]
