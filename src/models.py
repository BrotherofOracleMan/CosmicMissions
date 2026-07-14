from datetime import date
from decimal import Decimal
from sqlalchemy import Boolean, Date, Integer, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

class CosmicMission(Base):
    __tablename__ = "cosmic_missions"

    mission_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mission_name: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(255))
    launch_date: Mapped[date] = mapped_column(Date)
    crew_size: Mapped[int]= mapped_column(Integer)
    budget_billions: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_successful: Mapped[bool] = mapped_column(Boolean)
    telemetry_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    crew_members: Mapped[list["CrewMember"]] = relationship(back_populates="mission")

class CrewMember(Base):
    __tablename__ = "crew_members"

    crew_member_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mission_id: Mapped[int] = mapped_column(Integer, ForeignKey("cosmic_missions.mission_id"))
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(255))

    mission: Mapped["CosmicMission"] = relationship(back_populates="crew_members")