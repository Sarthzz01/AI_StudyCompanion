from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User, Role, Profile
from app.schemas.auth import (
    RegisterRequest, LoginRequest, Token, UserAuthResponse,
    ForgotPasswordRequest, ResetPasswordRequest, PasswordResetResponse
)
from app.services.auth_service import (
    hash_password, verify_password, create_access_token,
    create_password_reset_token, verify_password_reset_token
)
from app.services.email_service import send_password_reset_email
from app.services.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

def format_user_auth(user: User) -> UserAuthResponse:
    profile = user.profile
    name = profile.full_name if profile else user.email.split("@")[0]
    role_name = user.role.name if user.role else "student"
    joined_date = user.created_at.strftime("%B %Y") if user.created_at else "September 2026"
    return UserAuthResponse(
        id=str(user.id),
        name=name,
        email=user.email,
        role=role_name,
        joined=joined_date
    )

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # Check if email already registered
    existing_user = db.query(User).filter(User.email == request.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )
    
    # Resolve role (default: student)
    role_name = (request.role or "student").lower()
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        # Fallback to student role
        role = db.query(Role).filter(Role.name == "student").first()
        if not role:
            role = Role(name="student", description="Student account")
            db.add(role)
            db.commit()
            db.refresh(role)
            
    hashed_pwd = hash_password(request.password)
    user = User(
        email=request.email.lower(),
        hashed_password=hashed_pwd,
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create profile
    profile = Profile(
        user_id=user.id,
        full_name=request.name.strip(),
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

    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": role.name})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=format_user_auth(user)
    )

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please try again.",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )
        
    role_name = user.role.name if user.role else "student"
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": role_name})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=format_user_auth(user)
    )

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out. Client should discard token."}

@router.get("/me", response_model=UserAuthResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return format_user_auth(current_user)

@router.post("/forgot-password", response_model=PasswordResetResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email_clean = request.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    dev_link = None
    if user and user.is_active:
        token = create_password_reset_token(email=user.email, expires_minutes=30)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        _, dev_link = send_password_reset_email(user.email, reset_url)

    return PasswordResetResponse(
        message="If your email is registered with us, a password reset link has been sent to your inbox.",
        dev_reset_link=dev_link
    )

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The password reset link is invalid or has expired. Please request a new link."
        )

    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    user.hashed_password = hash_password(request.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Your password has been successfully reset. You can now log in."}

