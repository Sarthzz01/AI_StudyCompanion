from fastapi import APIRouter, Depends
from app.schemas.ai import AIPromptRequest, AIResponse
from app.services.ai_service import ai_service
from app.services.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["AI Service"])

@router.get("/health")
def ai_health():
    return {
        "status": "online",
        "configured": ai_service.is_configured(),
        "model": ai_service.model_name,
        "message": "Gemini AI service foundation active." if ai_service.is_configured() else "Demo fallback active (GEMINI_API_KEY not configured in backend/.env)."
    }

@router.post("/test", response_model=AIResponse)
def ai_test(req: AIPromptRequest, current_user: User = Depends(get_current_user)):
    result = ai_service.generate_text(prompt=req.prompt, system_instruction=req.system_instruction)
    return AIResponse(**result)
