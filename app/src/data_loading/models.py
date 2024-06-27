"""
Data models to define the expected API reply and data validation using the `pydantic` library.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    AwareDatetime,
    field_serializer,
)
from enum import StrEnum, auto


class Granularity(StrEnum):
    """
    Granularity options.
    """

    raw = auto()
    hourly = auto()
    life_time = "life-time"


class NoiseRequestParams(BaseModel):
    """
    Model for data in API request made for getting noise measurements.
    """

    granularity: Granularity = Granularity.raw
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    page: Optional[int] = Field(default=None, ge=0)

    @field_serializer("start")
    def serialize_dt(self, start: datetime, _info):
        return start.strftime("%Y-%m-%dT%H:%i:%s")

    @field_serializer("end")
    def serialize_dt(self, end: datetime, _info):
        return end.strftime("%Y-%m-%dT%H:%i:%s")


class Location(BaseModel):
    """
    Single location model.
    """

    id: str
    label: str
    latitude: float
    longitude: float
    radius: int | float
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
    Point-in-time noise measurement value with timestamp.
    """

    timestamp: AwareDatetime


class NoiseAggregate(Noise):
    """
    Aggregate noise measurement corresponding to a time interval.
    """

    start: Optional[datetime] = None
    end: Optional[datetime] = None
    count: int


class AbstractLocationNoiseData(BaseModel):
    """
    Abstract class for collecting noise data.
    """

    measurements: List[Noise]


class TimedLocationNoiseData(AbstractLocationNoiseData):
    """
    Timed location noise data.
    """

    measurements: List[NoiseTimed]


class AggregateLocationNoiseData(AbstractLocationNoiseData):
    """
    Aggregate noise data for a location.
    """

    measurements: List[NoiseAggregate]
