import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.material import Material
from app.models.document import DocumentChunk
from app.models.study import Quiz, Question, QuizAttempt, QuizAnswer, Performance, Notification
from app.models.learner import LearnerModel, Progress
from app.schemas.quiz import (
    QuizGenerateRequest,
    QuestionOut,
    QuizOut,
    QuizAttemptStartOut,
    QuizSubmitRequest,
    QuizAnswerReviewOut,
    QuizAttemptResultOut,
    QuizAttemptSummaryOut
)
from app.services.deps import get_current_user
from app.services.ai_service import ai_service

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["Quizzes"])

def _format_question(q: Question) -> QuestionOut:
    return QuestionOut(
        id=q.id,
        question=q.question_text,
        question_type=q.question_type or "multiple_choice",
        options=q.options_json or [],
        topic=q.topic_name or "General",
        difficulty=q.difficulty or "medium"
    )

def _format_quiz(quiz: Quiz) -> QuizOut:
    mat_title = quiz.material.title if quiz.material else None
    return QuizOut(
        id=quiz.id,
        material_id=quiz.material_id,
        material_title=mat_title,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        question_count=quiz.question_count,
        created_at=quiz.created_at.strftime("%Y-%m-%d %H:%M") if quiz.created_at else "Recently",
        questions=[_format_question(q) for q in quiz.questions]
    )

# =========================================================================
# 1. QUIZ GENERATION & RETRIEVAL
# =========================================================================

@router.post("/api/quizzes/generate", response_model=QuizOut, status_code=status.HTTP_201_CREATED)
def generate_quiz(
    payload: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate difficulty-aware multiple choice questions using Gemini based on study material.
    Stores Quiz and Question records in the database.
    """
    mat_id = payload.get_material_id()
    if not mat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="material_id is required to generate a quiz."
        )

    material = db.query(Material).filter(Material.id == mat_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study material '{mat_id}' not found."
        )

    # Context collection from DocumentChunks
    chunks = db.query(DocumentChunk).filter(DocumentChunk.material_id == material.id).order_by(DocumentChunk.chunk_index).all()
    topic = payload.topic or "All topics"
    if chunks:
        if topic != "All topics":
            topic_lower = topic.lower()
            matching = [c.content for c in chunks if topic_lower in c.content.lower()]
            content_text = "\n\n".join(matching) if matching else "\n\n".join([c.content for c in chunks[:5]])
        else:
            content_text = "\n\n".join([c.content for c in chunks[:5]])
    else:
        content_text = material.content_text or material.description or material.title

    count = max(1, min(payload.count or 5, 20))
    difficulty = payload.difficulty or "mixed"

    raw_questions = ai_service.generate_quiz_questions(
        material_title=material.title,
        content_text=content_text,
        topic=topic,
        difficulty=difficulty,
        count=count
    )

    # Create Quiz record
    quiz = Quiz(
        user_id=current_user.id,
        material_id=material.id,
        topic=topic,
        difficulty=difficulty,
        question_count=len(raw_questions),
        created_at=datetime.utcnow()
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    from app.models.subject import Topic
    topic_rec = db.query(Topic).filter(Topic.name.ilike(f"%{topic[:30]}%")).first() if topic != "All topics" else None
    topic_id_val = topic_rec.id if topic_rec else None

    # Create Question records
    created_questions = []
    for q_data in raw_questions:
        q_record = Question(
            quiz_id=quiz.id,
            topic_id=topic_id_val,
            material_id=material.id,
            topic_name=q_data.get("topic") or topic or material.title,
            question_text=q_data["question"],
            question_type="multiple_choice",
            options_json=q_data["options"],
            correct_answer=str(q_data["correct_answer"]),
            explanation=q_data.get("explanation", ""),
            difficulty=q_data.get("difficulty", difficulty if difficulty != "mixed" else "medium"),
            created_at=datetime.utcnow()
        )
        db.add(q_record)
        created_questions.append(q_record)

    db.commit()
    db.refresh(quiz)

    logger.info(f"Created Quiz {quiz.id} with {len(created_questions)} questions for material '{material.id}'.")
    return _format_quiz(quiz)

@router.get("/api/quizzes", response_model=List[QuizOut])
def list_quizzes(
    material_id: Optional[str] = Query(None, alias="materialId"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List quizzes accessible to the user."""
    query = db.query(Quiz).filter(Quiz.user_id == current_user.id)
    if material_id:
        query = query.filter(Quiz.material_id == material_id)
    quizzes = query.order_by(Quiz.created_at.desc()).all()
    return [_format_quiz(q) for q in quizzes]

@router.get("/api/quizzes/{id}", response_model=QuizOut)
def get_quiz(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve quiz details and questions by Quiz ID."""
    quiz = db.query(Quiz).filter(Quiz.id == id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz with ID {id} not found."
        )
    return _format_quiz(quiz)

# =========================================================================
# 2. QUIZ ATTEMPTS & SUBMISSION
# =========================================================================

@router.post("/api/quizzes/{id}/attempt", response_model=QuizAttemptStartOut, status_code=status.HTTP_201_CREATED)
def start_quiz_attempt(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start an in-progress attempt for a quiz.
    Returns attempt ID and questions ready for student answering.
    """
    quiz = db.query(Quiz).filter(Quiz.id == id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz with ID {id} not found."
        )

    mat_title = quiz.material.title if quiz.material else "Study Material"

    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        material_id=quiz.material_id,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        score=0,
        total_questions=len(quiz.questions),
        accuracy=0.0,
        status="in_progress",
        answers_json=[],
        topic_results_json={},
        difficulty_results_json={},
        created_at=datetime.utcnow()
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return QuizAttemptStartOut(
        id=attempt.id,
        quiz_id=quiz.id,
        material_id=quiz.material_id,
        material_title=mat_title,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        status="in_progress",
        questions=[_format_question(q) for q in quiz.questions]
    )

@router.get("/api/quiz-attempts/{id}")
def get_quiz_attempt(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve quiz attempt state and results."""
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.id == id,
        QuizAttempt.user_id == current_user.id
    ).first()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz attempt with ID {id} not found."
        )

    mat_title = attempt.material.title if attempt.material else "Study Material"

    # If completed, format full result
    if attempt.status == "completed":
        answers = db.query(QuizAnswer).filter(QuizAnswer.attempt_id == attempt.id).all()
        review = [
            QuizAnswerReviewOut(
                id=a.question_id or a.id,
                question=a.question_text,
                topic=a.topic or attempt.topic or "General",
                options=a.options_json or [],
                selected=a.selected_option,
                answer=a.correct_answer,
                correct=a.is_correct,
                explanation=a.explanation or ""
            )
            for a in answers
        ]

        topic_results = attempt.topic_results_json or {}
        difficulty_results = attempt.difficulty_results_json or {}

        strong = [t for t, v in topic_results.items() if v.get("total", 0) > 0 and (v.get("correct", 0) / v.get("total", 1)) >= 0.7]
        weak = [t for t, v in topic_results.items() if v.get("total", 0) > 0 and (v.get("correct", 0) / v.get("total", 1)) < 0.7]

        return QuizAttemptResultOut(
            id=str(attempt.id),
            quiz_id=attempt.quiz_id or 0,
            material_id=attempt.material_id,
            material_title=mat_title,
            topic=attempt.topic or "All topics",
            difficulty=attempt.difficulty or "mixed",
            score=attempt.score,
            total=attempt.total_questions,
            accuracy=attempt.accuracy,
            date=attempt.completed_at.strftime("%Y-%m-%d") if attempt.completed_at else datetime.utcnow().strftime("%Y-%m-%d"),
            topicResults=topic_results,
            strongTopics=strong,
            weakTopics=weak,
            difficultyResults=difficulty_results,
            review=review
        )

    # In progress
    quiz = attempt.quiz
    questions = [_format_question(q) for q in quiz.questions] if quiz else []
    return QuizAttemptStartOut(
        id=attempt.id,
        quiz_id=attempt.quiz_id or 0,
        material_id=attempt.material_id,
        material_title=mat_title,
        topic=attempt.topic or "All topics",
        difficulty=attempt.difficulty or "mixed",
        status="in_progress",
        questions=questions
    )

@router.post("/api/quiz-attempts/{id}/submit", response_model=QuizAttemptResultOut)
def submit_quiz_attempt(
    id: int,
    payload: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit and evaluate a quiz attempt.
    Calculates: accuracy, correct/incorrect answers, topic performance, and difficulty performance.
    Stores QuizAnswer and Performance records, and updates the LearnerModel and Progress.
    """
    attempt = db.query(QuizAttempt).filter(
        QuizAttempt.id == id,
        QuizAttempt.user_id == current_user.id
    ).first()
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz attempt with ID {id} not found."
        )

    quiz = attempt.quiz
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent quiz not found for this attempt."
        )

    questions_by_id = {q.id: q for q in quiz.questions}
    submitted_map = {item.question_id: item.selected_option for item in payload.answers}

    was_already_completed = (attempt.status == "completed")

    # Delete previous answers if re-submitting
    db.query(QuizAnswer).filter(QuizAnswer.attempt_id == attempt.id).delete()
    db.query(Performance).filter(Performance.quiz_attempt_id == attempt.id).delete()

    correct_count = 0
    total_count = len(quiz.questions)
    topic_results: Dict[str, Dict[str, Any]] = {}
    difficulty_results: Dict[str, Dict[str, Any]] = {}
    review_items: List[QuizAnswerReviewOut] = []
    saved_answers = []

    for q in quiz.questions:
        selected_option = submitted_map.get(q.id)
        try:
            correct_idx = int(q.correct_answer)
        except (ValueError, TypeError):
            correct_idx = 0

        is_correct = (selected_option is not None and int(selected_option) == correct_idx)
        if is_correct:
            correct_count += 1

        from app.services.learner_service import learner_service
        raw_topic = q.topic_name or attempt.topic or "General"
        topic_name = learner_service.normalize_topic_name(raw_topic, db=db)
        diff = q.difficulty or "medium"

        # Topic aggregation
        if topic_name not in topic_results:
            topic_results[topic_name] = {"correct": 0, "total": 0}
        topic_results[topic_name]["total"] += 1
        if is_correct:
            topic_results[topic_name]["correct"] += 1

        # Difficulty aggregation
        if diff not in difficulty_results:
            difficulty_results[diff] = {"correct": 0, "total": 0}
        difficulty_results[diff]["total"] += 1
        if is_correct:
            difficulty_results[diff]["correct"] += 1

        # Create QuizAnswer record
        answer_rec = QuizAnswer(
            attempt_id=attempt.id,
            question_id=q.id,
            question_text=q.question_text,
            options_json=q.options_json or [],
            selected_option=selected_option,
            correct_answer=correct_idx,
            is_correct=is_correct,
            explanation=q.explanation or "",
            topic=topic_name,
            difficulty=diff,
            created_at=datetime.utcnow()
        )
        db.add(answer_rec)
        saved_answers.append(answer_rec)

        review_items.append(QuizAnswerReviewOut(
            id=q.id,
            question=q.question_text,
            topic=topic_name,
            options=q.options_json or [],
            selected=selected_option,
            answer=correct_idx,
            correct=is_correct,
            explanation=q.explanation or ""
        ))

    accuracy = round((correct_count / total_count * 100), 1) if total_count > 0 else 0.0
    incorrect_count = total_count - correct_count

    # Calculate percentage for each topic & difficulty
    for t_data in topic_results.values():
        t_data["accuracy"] = round((t_data["correct"] / t_data["total"]) * 100, 1) if t_data["total"] > 0 else 0.0
    for d_data in difficulty_results.values():
        d_data["accuracy"] = round((d_data["correct"] / d_data["total"]) * 100, 1) if d_data["total"] > 0 else 0.0

    strong_topics = [t for t, v in topic_results.items() if (v["correct"] / v["total"]) >= 0.7]
    weak_topics = [t for t, v in topic_results.items() if (v["correct"] / v["total"]) < 0.7]

    # Create Performance record
    performance = Performance(
        user_id=current_user.id,
        quiz_attempt_id=attempt.id,
        accuracy=accuracy,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        topic_performance_json=topic_results,
        difficulty_performance_json=difficulty_results,
        created_at=datetime.utcnow()
    )
    db.add(performance)

    # Update QuizAttempt
    attempt.score = correct_count
    attempt.total_questions = total_count
    attempt.accuracy = accuracy
    attempt.status = "completed"
    attempt.completed_at = datetime.utcnow()
    attempt.answers_json = [
        {"question_id": a.question_id, "selected_option": a.selected_option, "is_correct": a.is_correct}
        for a in saved_answers
    ]
    attempt.topic_results_json = topic_results
    attempt.difficulty_results_json = difficulty_results

    # Update LearnerModel and SM-2 Revision Schedules for each tested topic
    from app.services.learner_service import learner_service
    from app.services.revision_service import revision_service
    for topic_name, res in topic_results.items():
        learner_service.update_topic_after_quiz(
            db=db,
            user_id=current_user.id,
            topic_name=topic_name,
            score=res["correct"],
            total=res["total"],
            difficulty=attempt.difficulty or "medium"
        )
        revision_service.update_revision_after_quiz(
            db=db,
            user_id=current_user.id,
            topic_name=topic_name,
            score=res["correct"],
            total=res["total"],
            material_id=attempt.material_id
        )

    # Update User Progress and Study Session
    from app.models.study import StudySession
    study_mins = max(2, total_count * 2)
    session = StudySession(
        user_id=current_user.id,
        material_id=attempt.material_id,
        duration_minutes=study_mins,
        session_type="quiz",
        topic=attempt.topic,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow()
    )
    db.add(session)

    progress = db.query(Progress).filter(Progress.user_id == current_user.id).first()
    if not progress:
        progress = Progress(
            user_id=current_user.id,
            overall_accuracy=accuracy,
            questions_attempted=total_count,
            total_study_time_minutes=study_mins,
            quizzes_completed=1,
            last_active=datetime.utcnow(),
            history_json=[{
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "accuracy": accuracy,
                "score": correct_count,
                "total": total_count
            }]
        )
        db.add(progress)
    else:
        prev_attempts = progress.questions_attempted or 0
        prev_correct = round(((progress.overall_accuracy or 0.0) / 100.0) * prev_attempts)
        new_attempts = prev_attempts + total_count
        new_correct = prev_correct + correct_count
        progress.questions_attempted = new_attempts
        progress.total_study_time_minutes = (progress.total_study_time_minutes or 0) + study_mins
        progress.quizzes_completed = (progress.quizzes_completed or 0) + 1
        progress.overall_accuracy = round((new_correct / new_attempts) * 100, 1) if new_attempts > 0 else accuracy
        progress.last_active = datetime.utcnow()

        history = list(progress.history_json or [])
        history.append({
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "accuracy": accuracy,
            "score": correct_count,
            "total": total_count
        })
        progress.history_json = history[-15:]

    # Create persistent Notification (with duplicate prevention)
    if not was_already_completed:
        topic_label = attempt.topic or (quiz.material.title if quiz and quiz.material else "Quiz")
        notif = Notification(
            user_id=current_user.id,
            title="Quiz Completed",
            message=f"{topic_label}: Scored {correct_count}/{total_count} ({accuracy}% accuracy).",
            type="quiz",
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(notif)

    db.commit()
    db.refresh(attempt)

    mat_title = attempt.material.title if attempt.material else (quiz.material.title if quiz.material else "Study Material")

    return QuizAttemptResultOut(
        id=str(attempt.id),
        quiz_id=quiz.id,
        material_id=attempt.material_id,
        material_title=mat_title,
        topic=attempt.topic or "All topics",
        difficulty=attempt.difficulty or "mixed",
        score=correct_count,
        total=total_count,
        accuracy=accuracy,
        date=attempt.completed_at.strftime("%Y-%m-%d") if attempt.completed_at else datetime.utcnow().strftime("%Y-%m-%d"),
        topicResults=topic_results,
        strongTopics=strong_topics,
        weakTopics=weak_topics,
        difficultyResults=difficulty_results,
        review=review_items
    )

@router.get("/api/quiz-attempts", response_model=List[QuizAttemptSummaryOut])
def list_quiz_attempts(
    material_id: Optional[str] = Query(None, alias="materialId"),
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve historical completed quiz attempts for student dashboard / sidebar."""
    query = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id,
        QuizAttempt.status == "completed"
    )
    if material_id:
        query = query.filter(QuizAttempt.material_id == material_id)
    attempts = query.order_by(QuizAttempt.completed_at.desc(), QuizAttempt.id.desc()).limit(limit).all()

    out = []
    for a in attempts:
        mat_title = a.material.title if a.material else "Study Material"
        out.append(QuizAttemptSummaryOut(
            id=str(a.id),
            quiz_id=a.quiz_id,
            material_id=a.material_id,
            material_title=mat_title,
            topic=a.topic or "All topics",
            difficulty=a.difficulty or "mixed",
            score=a.score,
            total=a.total_questions,
            accuracy=a.accuracy,
            date=a.completed_at.strftime("%Y-%m-%d") if a.completed_at else (a.created_at.strftime("%Y-%m-%d") if a.created_at else "Recently"),
            status=a.status
        ))
    return out
