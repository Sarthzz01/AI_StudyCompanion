from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Profile
from app.schemas.profile import ProfileOut, ProfileUpdate, PasswordChangeRequest
from app.services.auth_service import hash_password, verify_password
from app.services.deps import get_current_user

from sqlalchemy.orm.attributes import flag_modified

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("", response_model=ProfileOut)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = current_user.profile
    if not profile:
        profile = Profile(
            user_id=current_user.id,
            full_name=current_user.email.split("@")[0],
            preferences_json={
                "difficulty": "medium",
                "sessionLength": "30",
                "quizAlerts": True,
                "goalAlerts": True,
                "weeklySummary": False
            }
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return ProfileOut(
        id=profile.id,
        user_id=current_user.id,
        full_name=profile.full_name,
        email=current_user.email,
        role=current_user.role.name if current_user.role else "student",
        avatar_url=profile.avatar_url,
        bio=profile.bio,
        joined=current_user.created_at.strftime("%B %Y") if current_user.created_at else "September 2026",
        preferences=profile.preferences_json or {}
    )

@router.put("", response_model=ProfileOut)
def update_profile(
    updates: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = current_user.profile
    if not profile:
        profile = Profile(user_id=current_user.id, full_name=current_user.email.split("@")[0])
        db.add(profile)

    if updates.name is not None and updates.name.strip():
        profile.full_name = updates.name.strip()
    if updates.bio is not None:
        profile.bio = updates.bio.strip()
    if updates.avatar_url is not None:
        profile.avatar_url = updates.avatar_url
    if updates.preferences is not None:
        # Merge preferences
        current_prefs = dict(profile.preferences_json or {})
        current_prefs.update(updates.preferences)
        profile.preferences_json = current_prefs
        flag_modified(profile, "preferences_json")

    db.commit()
    db.refresh(profile)

    return ProfileOut(
        id=profile.id,
        user_id=current_user.id,
        full_name=profile.full_name,
        email=current_user.email,
        role=current_user.role.name if current_user.role else "student",
        avatar_url=profile.avatar_url,
        bio=profile.bio,
        joined=current_user.created_at.strftime("%B %Y") if current_user.created_at else "September 2026",
        preferences=profile.preferences_json or {}
    )

@router.put("/password")
def change_password(
    req: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    
    if len(req.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long.",
        )
        
    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"message": "Password changed successfully."}
