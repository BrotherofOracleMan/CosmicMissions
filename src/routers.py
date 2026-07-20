from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import CosmicMission, CrewMember
from schemas import CosmicMissionBase, CosmicMissionCreate, CosmicMissionPut, CosmicMissionUpdate, CrewMemberBase, CrewMemberCreate
from auth import get_api_key

router = APIRouter(prefix="/cosmic-missions", tags=["cosmic-missions"], dependencies=[Depends(get_api_key)])

@router.get("", response_model=list[CosmicMissionBase])
def get_cosmic_missions(db: Session = Depends(get_db)):
    return db.query(CosmicMission).all()

@router.get("/success", response_model=list[CosmicMissionBase])
def get_all_successfull_missions(db:Session = Depends(get_db)):
    return db.query(CosmicMission).filter(CosmicMission.is_successful == True).all()

@router.get("/{mission_id}", response_model=CosmicMissionBase)
def get_cosmic_mission_by_id(mission_id: int, db: Session = Depends(get_db)):
    mission_row = db.query(CosmicMission).filter(CosmicMission.mission_id == mission_id).first()
    if not mission_row:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission_row

@router.get("/{mission_id}/telemetry", response_model=dict | None)
def get_telemetry_data_by_mission_id(mission_id: int, db: Session = Depends(get_db)):
    mission_row = db.query(CosmicMission).filter(CosmicMission.mission_id == mission_id).first()
    if not mission_row:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission_row.telemetry_data

@router.put("/{mission_id}", response_model=CosmicMissionBase)
def update_cosmic_mission(mission_id: int, mission: CosmicMissionPut, db: Session = Depends(get_db)):
    db_mission = db.query(CosmicMission).filter(CosmicMission.mission_id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    db_mission.mission_name = mission.mission_name
    db_mission.destination = mission.destination
    db_mission.launch_date = mission.launch_date
    db_mission.crew_size = mission.crew_size
    db_mission.budget_billions = mission.budget_billions
    db_mission.is_successful = mission.is_successful
    db_mission.telemetry_data = mission.telemetry_data
    db.commit()
    db.refresh(db_mission)
    return db_mission


@router.patch("/{mission_id}", response_model=CosmicMissionBase)
def patch_cosmic_mission(mission_id: int, mission: CosmicMissionUpdate, db: Session = Depends(get_db)):
    db_mission = db.query(CosmicMission).filter(CosmicMission.mission_id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if "mission_name" in mission.model_fields_set:
        db_mission.mission_name = mission.mission_name
    if "destination" in mission.model_fields_set:
        db_mission.destination = mission.destination
    if "launch_date" in mission.model_fields_set:
        db_mission.launch_date = mission.launch_date
    if "crew_size" in mission.model_fields_set:
        db_mission.crew_size = mission.crew_size
    if "budget_billions" in mission.model_fields_set:
        db_mission.budget_billions = mission.budget_billions
    if "is_successful" in mission.model_fields_set:
        db_mission.is_successful = mission.is_successful
    if "telemetry_data" in mission.model_fields_set:
        db_mission.telemetry_data = mission.telemetry_data
    db.commit()
    db.refresh(db_mission)
    return db_mission

@router.post("", response_model = CosmicMissionBase)
def create_cosmic_mission(mission: CosmicMissionCreate, db: Session = Depends(get_db)):
    db_mission = CosmicMission(
        mission_id=mission.mission_id,
        mission_name=mission.mission_name,
        destination=mission.destination,
        launch_date=mission.launch_date,
        crew_size=mission.crew_size,
        budget_billions=mission.budget_billions,
        is_successful=mission.is_successful,
        telemetry_data=mission.telemetry_data
    )
    db.add(db_mission)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Mission with this ID already exists")
    db.refresh(db_mission)
    return db_mission

@router.delete("/{mission_id}", response_model=dict)
def delete_cosmic_mission(mission_id:int, db:Session = Depends(get_db)):
    db_mission = db.query(CosmicMission).filter(CosmicMission.mission_id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    db.delete(db_mission)
    db.commit()
    return {"message": "Mission deleted successfully"}


@router.post("/{mission_id}/crew", response_model=CrewMemberBase)
def add_crew_member_to_mission(mission_id: int, crew_member: CrewMemberCreate, db: Session = Depends(get_db)):
    db_mission = db.query(CosmicMission).filter(CosmicMission.mission_id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    db_crew_member = CrewMember(
        mission_id=mission_id,
        name=crew_member.name,
        role=crew_member.role
    )
    try:
        db.add(db_crew_member)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Crew member with this ID already exists")
    db.refresh(db_crew_member)
    return db_crew_member

@router.get("/{mission_id}/crew", response_model=list[CrewMemberBase])
def get_crew_members_by_mission_id(mission_id: int, db: Session = Depends(get_db)):
    db_mission = db.query(CosmicMission).filter(CosmicMission.mission_id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return db_mission.crew_members

@router.delete("/{mission_id}/crew/{crew_member_id}", response_model=dict)
def delete_crew_member_from_mission(mission_id: int, crew_member_id: int, db: Session = Depends(get_db)):
    db_mission = db.query(CosmicMission).filter(CosmicMission.mission_id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    db_crew_member = db.query(CrewMember).filter(CrewMember.crew_member_id == crew_member_id, CrewMember.mission_id == mission_id).first()
    if not db_crew_member:
        raise HTTPException(status_code=404, detail="Crew member not found")
    db.delete(db_crew_member)
    db.commit()
    return {"message": "Crew member deleted successfully"}