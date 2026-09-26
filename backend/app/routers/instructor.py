import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger("uvicorn.error")

from app.database import get_db
from app.models.user import User
from app.services.deps import get_current_user, require_roles
from app.services.instructor_service import instructor_service
from app.services.ai_service import ai_service
from app.schemas.instructor import (
    AssessmentCreateRequest,
    AssessmentUpdateRequest,
    AssessmentResponse,
    AssignAssessmentRequest,
    AssignmentResponse,
    StudentSummaryItem,
    StudentDetailResponse,
    CreateFeedbackRequest,
    FeedbackResponse,
    ClassAnalyticsOverview,
    ClassSummaryReport,
    AIGenerateQuestionsRequest,
    AIGenerateQuestionsResponse,
    SubmitAssessmentRequest,
    AssessmentSubmissionResponse
)
from app.models.assessment import Assessment, AssessmentAssignment, AssessmentSubmission
from app.models.material import Material
from app.services.learner_service import learner_service

router = APIRouter(prefix="/instructor", tags=["Instructor Module"])
student_assessments_router = APIRouter(prefix="/assessments", tags=["Student Assessments"])

# ==========================================
# 1. Instructor Dashboard & KPIs
# ==========================================

@router.get("/dashboard")
def get_instructor_dashboard(
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    return instructor_service.get_dashboard_summary(db, current_user.id)

# ==========================================
# 2. Student List & Student Deep-Dive
# ==========================================

@router.get("/students", response_model=List[StudentSummaryItem])
def list_students(
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    return instructor_service.list_students(db)

@router.get("/students/{student_id}", response_model=StudentDetailResponse)
def get_student_detail(
    student_id: int,
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    detail = instructor_service.get_student_detail(db, student_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")
    return detail

# ==========================================
# 3. Assessment Management
# ==========================================

@router.get("/assessments", response_model=List[AssessmentResponse])
def list_assessments(
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    return instructor_service.list_assessments(db, current_user.id)

@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    request: AssessmentCreateRequest,
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    assessment = instructor_service.create_assessment(db, current_user.id, request)
    return instructor_service.get_assessment(db, assessment.id)

@router.get("/assessments/{assessment_id}")
def get_assessment(
    assessment_id: int,
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    data = instructor_service.get_assessment(db, assessment_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
    return data

@router.put("/assessments/{assessment_id}", response_model=AssessmentResponse)
def update_assessment(
    assessment_id: int,
    request: AssessmentUpdateRequest,
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    updated = instructor_service.update_assessment(db, assessment_id, request)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
    return instructor_service.get_assessment(db, updated.id)

@router.delete("/assessments/{assessment_id}", status_code=status.HTTP_200_OK)
def delete_assessment(
    assessment_id: int,
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    success = instructor_service.delete_assessment(db, assessment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
    return {"message": "Assessment successfully deleted."}

# ==========================================
# 4. Assessment Assignments
# ==========================================

@router.post("/assessments/{assessment_id}/assign", response_model=AssignmentResponse)
def assign_assessment(
    assessment_id: int,
    request: AssignAssessmentRequest,
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
    
    asgn = instructor_service.assign_assessment(db, assessment_id, current_user.id, request)
    return {
        "id": asgn.id,
        "assessment_id": asgn.assessment_id,
        "assessment_title": assessment.title,
        "topic": assessment.topic,
        "instructor_id": asgn.instructor_id,
        "assigned_to_all": asgn.assigned_to_all,
        "student_id": asgn.student_id,
        "student_name": asgn.student.profile.full_name if (asgn.student and asgn.student.profile) else None,
        "due_date": asgn.due_date,
        "instructions": asgn.instructions,
        "status": asgn.status,
        "created_at": asgn.created_at,
        "submissions_count": 0
    }

@router.get("/assignments", response_model=List[AssignmentResponse])
def list_assignments(
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    return instructor_service.list_assignments(db, current_user.id)

# ==========================================
# 5. Class Analytics & Reports
# ==========================================

@router.get("/analytics/overview", response_model=ClassAnalyticsOverview)
def get_class_analytics(
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    return instructor_service.get_class_analytics(db)

@router.get("/reports/class-summary", response_model=ClassSummaryReport)
def get_class_summary_report(
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    inst_name = current_user.profile.full_name if current_user.profile else "Instructor"
    return instructor_service.generate_class_report(db, inst_name)

# ==========================================
# 6. Feedback System
# ==========================================

@router.get("/feedback", response_model=List[FeedbackResponse])
def list_feedback(
    student_id: Optional[int] = None,
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    return instructor_service.list_feedbacks(db, instructor_id=current_user.id, student_id=student_id)

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    request: CreateFeedbackRequest,
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    fb = instructor_service.create_feedback(db, current_user.id, request)
    inst_name = current_user.profile.full_name if current_user.profile else "Instructor"
    stud_user = db.query(User).filter(User.id == fb.student_id).first()
    stud_name = stud_user.profile.full_name if (stud_user and stud_user.profile) else (stud_user.email if stud_user else "Student")

    return FeedbackResponse(
        id=fb.id,
        instructor_id=fb.instructor_id,
        instructor_name=inst_name,
        student_id=fb.student_id,
        student_name=stud_name,
        student_email=stud_user.email if stud_user else "",
        assessment_id=fb.assessment_id,
        assessment_title=fb.assessment.title if fb.assessment else None,
        topic=fb.topic,
        feedback_type=fb.feedback_type,
        feedback_text=fb.feedback_text,
        action_items=fb.action_items_json or [],
        is_read=fb.is_read,
        created_at=fb.created_at
    )

# ==========================================
# 7. AI Question Generator for Instructors
# ==========================================

@router.post("/ai/generate-questions", response_model=AIGenerateQuestionsResponse)
def ai_generate_assessment_questions(
    request: AIGenerateQuestionsRequest,
    current_user: User = Depends(require_roles(["instructor", "admin"])),
    db: Session = Depends(get_db)
):
    # Fetch material context if material_id provided
    material_context = None
    if request.material_id:
        mat = db.query(Material).filter(Material.id == request.material_id).first()
        if mat:
            material_context = mat.extracted_text

    ai_result = ai_service.generate_assessment_questions(
        topic=request.topic,
        subject=request.subject,
        difficulty=request.difficulty,
        question_count=request.question_count,
        material_context=material_context
    )
    return ai_result

# ==========================================
# 8. Student Assessment Endpoints (Student Portal)
# ==========================================

@student_assessments_router.get("/assigned")
def get_assigned_assessments_for_student(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all active assessments assigned to the current student or class.
    """
    assignments = (
        db.query(AssessmentAssignment)
        .filter(
            AssessmentAssignment.status == "active",
            (AssessmentAssignment.assigned_to_all == True) | (AssessmentAssignment.student_id == current_user.id)
        )
        .all()
    )
    results = []
    for asgn in assignments:
        a = asgn.assessment
        if not a or not a.is_published:
            continue
        # Check if already submitted
        sub = (
            db.query(AssessmentSubmission)
            .filter(AssessmentSubmission.assessment_id == a.id, AssessmentSubmission.student_id == current_user.id)
            .first()
        )
        results.append({
            "assignment_id": asgn.id,
            "assessment_id": a.id,
            "title": a.title,
            "topic": a.topic,
            "difficulty": a.difficulty,
            "time_limit_minutes": a.time_limit_minutes,
            "total_points": a.total_points,
            "pass_percentage": a.pass_percentage,
            "question_count": len(a.questions_json),
            "due_date": asgn.due_date,
            "instructions": asgn.instructions,
            "is_submitted": bool(sub),
            "submission_score": sub.score if sub else None,
            "submission_percentage": sub.percentage if sub else None,
            "passed": sub.passed if sub else None
        })
    return results

@student_assessments_router.get("/{assessment_id}")
def get_assessment_for_student(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns assessment questions for taking the assessment.
    Hides correct_answer indices to prevent client cheating.
    """
    a = db.query(Assessment).filter(Assessment.id == assessment_id, Assessment.is_published == True).first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")
    
    # Sanitize questions: omit correct_answer and explanation
    safe_questions = []
    for q in a.questions_json:
        safe_questions.append({
            "id": q.get("id"),
            "question_text": q.get("question_text"),
            "question_type": q.get("question_type", "multiple_choice"),
            "options": q.get("options", []),
            "points": q.get("points", 10),
            "difficulty": q.get("difficulty", "medium")
        })

    return {
        "id": a.id,
        "title": a.title,
        "description": a.description,
        "topic": a.topic,
        "difficulty": a.difficulty,
        "time_limit_minutes": a.time_limit_minutes,
        "total_points": a.total_points,
        "pass_percentage": a.pass_percentage,
        "question_count": len(safe_questions),
        "questions": safe_questions
    }

@student_assessments_router.post("/{assessment_id}/submit", response_model=AssessmentSubmissionResponse)
def submit_student_assessment(
    assessment_id: int,
    request: SubmitAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    # Grade the submission
    questions_map = {q.get("id"): q for q in a.questions_json}
    total_earned_points = 0.0
    total_possible_points = float(a.total_points)

    graded_answers = []
    for ans in request.answers:
        q = questions_map.get(ans.question_id)
        if q:
            is_correct = (ans.selected_option == q.get("correct_answer"))
            pts = q.get("points", 10)
            if is_correct:
                total_earned_points += pts
            graded_answers.append({
                "question_id": ans.question_id,
                "selected_option": ans.selected_option,
                "correct_answer": q.get("correct_answer"),
                "is_correct": is_correct,
                "points_earned": pts if is_correct else 0,
                "explanation": q.get("explanation")
            })

    percentage = (total_earned_points / max(1.0, total_possible_points)) * 100.0
    passed = percentage >= a.pass_percentage

    # Save submission
    sub = AssessmentSubmission(
        assessment_id=a.id,
        assignment_id=request.assignment_id,
        student_id=current_user.id,
        score=total_earned_points,
        total_points=a.total_points,
        percentage=round(percentage, 1),
        passed=passed,
        answers_json=graded_answers,
        time_spent_seconds=request.time_spent_seconds,
        status="graded"
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    # Sync with Learner Model
    try:
        learner_service.update_topic_after_quiz(
            db=db,
            user_id=current_user.id,
            topic_name=a.topic,
            score=int(total_earned_points),
            total=int(total_possible_points),
            difficulty=a.difficulty
        )
    except Exception as e:
        logger.warning(f"Learner sync after assessment submission warning: {e}")

    student_name = current_user.profile.full_name if current_user.profile else current_user.email

    return AssessmentSubmissionResponse(
        id=sub.id,
        assessment_id=a.id,
        assessment_title=a.title,
        student_id=current_user.id,
        student_name=student_name,
        student_email=current_user.email,
        score=sub.score,
        total_points=sub.total_points,
        percentage=sub.percentage,
        passed=sub.passed,
        time_spent_seconds=sub.time_spent_seconds,
        status=sub.status,
        submitted_at=sub.submitted_at,
        answers_count=len(graded_answers)
    )
