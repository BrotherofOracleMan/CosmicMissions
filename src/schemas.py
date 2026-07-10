from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from pydantic import Field

class CosmicMissionBase(BaseModel):
    mission_id: int
    mission_name: str
    destination: str
    launch_date: date
    crew_size: int
    budget_billions: Decimal
    is_successful: bool
    telemetry_data: dict | None = None

class CosmicMissionCreate(BaseModel):
    mission_id: int = Field(..., description="The ID of the cosmic mission")
    mission_name: str = Field(..., description="The name of the cosmic mission")
    destination: str = Field(..., description="The destination of the cosmic mission")
    launch_date: date = Field(default_factory=date.today, description="The launch date of the cosmic mission")
    crew_size: int = Field(default=0, description="The crew size of the cosmic mission")
    budget_billions: Decimal = Field(default=0.0, description="The budget of the cosmic mission")
    is_successful: bool = Field(default=False, description="Whether the mission was successful")
    telemetry_data: dict | None = Field(default=None, description="The telemetry data of the mission")

class CosmicMissionUpdate(BaseModel):
    mission_name: str | None = Field(default=None, description="The name of the cosmic mission")
    destination: str | None = Field(default=None, description="The destination of the cosmic mission")
    launch_date: date | None = Field(default=None, description="The launch date of the cosmic mission")
    crew_size: int | None = Field(default=None, description="The crew size of the cosmic mission")
    budget_billions: Decimal | None = Field(default=None, description="The budget of the cosmic mission")
    is_successful: bool | None = Field(default=None, description="Whether the mission was successful")
    telemetry_data: dict | None = Field(default=None, description="The telemetry data of the mission")


class CosmicMissionPut(BaseModel):
    mission_name: str = Field(..., description="The name of the cosmic mission")
    destination: str = Field(..., description="The destination of the cosmic mission")
    launch_date: date = Field(default_factory=date.today, description="The launch date of the cosmic mission")
    crew_size: int = Field(default=0, description="The crew size of the cosmic mission")
    budget_billions: Decimal = Field(default=0.0, description="The budget of the cosmic mission")
    is_successful: bool = Field(default=False, description="Whether the mission was successful")
    telemetry_data: dict | None = Field(default=None, description="The telemetry data of the mission")