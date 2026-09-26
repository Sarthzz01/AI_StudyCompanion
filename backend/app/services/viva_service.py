import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.viva import VivaSession, VivaQuestion, VivaAnswer, VivaEvaluation
from app.models.study import Notification
from app.models.material import Material
from app.models.document import DocumentChunk
from app.services.ai_service import ai_service
from app.services.learner_service import learner_service
from app.services.revision_service import revision_service

logger = logging.getLogger("uvicorn.error")


class VivaService:
    def _get_material_context(self, db: Session, material_id: Optional[str], topic: str) -> Optional[str]:
        """Retrieves text context from material or chunks to ground viva questions."""
        if not material_id:
            # Try to find a matching material for the topic
            mat = db.query(Material).all()
            for m in mat:
                top_names = [t.get("name", "").lower() for t in (m.topics_json or [])]
                if topic.lower() in top_names or any(topic.lower() in t for t in top_names):
                    material_id = m.id
                    break

        if not material_id:
            return None

        # Fetch chunks matching topic or first 2 chunks of material
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.material_id == material_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .limit(3)
            .all()
        )
        if chunks:
            return "\n\n".join(c.content for c in chunks if c.content)
        
        # Fallback to material content_text
        mat_obj = db.query(Material).filter(Material.id == material_id).first()
        if mat_obj and mat_obj.content_text:
            return mat_obj.content_text[:2000]
        return None

    def start_session(
        self,
        db: Session,
        user_id: int,
        topic: str,
        mode: str = "basic",
        difficulty: str = "medium",
        material_id: Optional[str] = None,
        total_questions: int = 4
    ) -> Dict[str, Any]:
        """
        Initializes a new viva session and generates the first question.
        """
        canonical_topic = learner_service.normalize_topic_name(topic, db)
        
        session = VivaSession(
            user_id=user_id,
            material_id=material_id,
            topic=canonical_topic,
            mode=mode.lower(),
            difficulty=difficulty.lower(),
            status="in_progress",
            current_question_index=1,
            total_questions=max(2, min(10, total_questions)),
            created_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Retrieve grounding context if available
        context_text = self._get_material_context(db, material_id, canonical_topic)

        # Generate Question 1
        q1_data = ai_service.generate_viva_question(
            topic=canonical_topic,
            mode=mode,
            difficulty=difficulty,
            question_index=1,
            context_text=context_text,
            previous_questions=[]
        )

        q1 = VivaQuestion(
            session_id=session.id,
            question_index=1,
            question_text=q1_data.get("question_text", f"Explain the core principles of {canonical_topic}."),
            topic=canonical_topic,
            difficulty=q1_data.get("difficulty", difficulty),
            question_type=q1_data.get("question_type", "main"),
            ideal_concept_points_json=q1_data.get("ideal_concept_points") or [f"Core concepts of {canonical_topic}"],
            created_at=datetime.utcnow()
        )
        db.add(q1)
        db.commit()
        db.refresh(q1)

        return {
            "session_id": session.id,
            "topic": session.topic,
            "material_id": session.material_id,
            "mode": session.mode,
            "difficulty": session.difficulty,
            "status": session.status,
            "current_question_index": 1,
            "total_questions": session.total_questions,
            "current_question": {
                "id": q1.id,
                "question_index": 1,
                "question_text": q1.question_text,
                "difficulty": q1.difficulty,
                "question_type": q1.question_type,
                "ideal_concept_points": q1.ideal_concept_points_json
            }
        }

    def submit_answer(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        question_id: int,
        answer_text: str
    ) -> Dict[str, Any]:
        """
        Records student answer, executes AI evaluation, and determines next question or follow-up.
        """
        session = db.query(VivaSession).filter(
            VivaSession.id == session_id,
            VivaSession.user_id == user_id
        ).first()
        if not session:
            raise ValueError("Viva session not found.")

        if session.status == "completed":
            raise ValueError("This viva session is already completed.")

        question = db.query(VivaQuestion).filter(
            VivaQuestion.id == question_id,
            VivaQuestion.session_id == session.id
        ).first()
        if not question:
            raise ValueError("Question not found for this session.")

        # Check if already answered
        existing_ans = db.query(VivaAnswer).filter(VivaAnswer.question_id == question.id).first()
        if existing_ans:
            db.delete(existing_ans)
            db.commit()

        # Save Answer
        answer = VivaAnswer(
            session_id=session.id,
            question_id=question.id,
            user_id=user_id,
            answer_text=answer_text.strip(),
            created_at=datetime.utcnow()
        )
        db.add(answer)
        db.commit()
        db.refresh(answer)

        # AI Evaluation
        eval_data = ai_service.evaluate_viva_answer(
            question_text=question.question_text,
            student_answer=answer.answer_text,
            topic=session.topic,
            mode=session.mode,
            ideal_concept_points=question.ideal_concept_points_json
        )

        evaluation = VivaEvaluation(
            session_id=session.id,
            question_id=question.id,
            answer_id=answer.id,
            score=eval_data["score"],
            correctness=eval_data["correctness"],
            relevance=eval_data["relevance"],
            completeness=eval_data["completeness"],
            conceptual_understanding=eval_data["conceptual_understanding"],
            feedback=eval_data["feedback"],
            key_strengths_json=eval_data["key_strengths"],
            missing_points_json=eval_data["missing_points"],
            suggested_follow_up_topic=eval_data.get("suggested_follow_up_topic", session.topic),
            created_at=datetime.utcnow()
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)

        # Determine whether to generate next question or conclude
        answered_count = db.query(VivaAnswer).filter(VivaAnswer.session_id == session.id).count()
        
        has_next = answered_count < session.total_questions
        next_q_data = None

        if has_next:
            next_idx = answered_count + 1
            session.current_question_index = next_idx

            # Check if an adaptive follow-up is appropriate
            needs_follow_up = eval_data.get("needs_follow_up", False) and len(eval_data.get("missing_points", [])) > 0
            
            if needs_follow_up and question.question_type == "main":
                # Generate Adaptive Follow-Up Question
                follow_up = ai_service.generate_viva_follow_up_question(
                    topic=session.topic,
                    previous_question=question.question_text,
                    student_answer=answer.answer_text,
                    missing_points=eval_data.get("missing_points", []),
                    mode=session.mode
                )
                next_q = VivaQuestion(
                    session_id=session.id,
                    question_index=next_idx,
                    question_text=follow_up.get("question_text"),
                    topic=session.topic,
                    difficulty=question.difficulty,
                    question_type="follow_up",
                    parent_question_id=question.id,
                    ideal_concept_points_json=follow_up.get("ideal_concept_points", []),
                    created_at=datetime.utcnow()
                )
            else:
                # Generate Next Main Question
                prev_questions = [q.question_text for q in session.questions]
                context_text = self._get_material_context(db, session.material_id, session.topic)
                
                # Adaptive difficulty: If student scored >= 85, increase challenge
                next_diff = "hard" if eval_data["score"] >= 85 else ("easy" if eval_data["score"] < 50 else session.difficulty)
                
                gen_q = ai_service.generate_viva_question(
                    topic=session.topic,
                    mode=session.mode,
                    difficulty=next_diff,
                    question_index=next_idx,
                    context_text=context_text,
                    previous_questions=prev_questions
                )
                next_q = VivaQuestion(
                    session_id=session.id,
                    question_index=next_idx,
                    question_text=gen_q.get("question_text"),
                    topic=session.topic,
                    difficulty=gen_q.get("difficulty", next_diff),
                    question_type="main",
                    ideal_concept_points_json=gen_q.get("ideal_concept_points", []),
                    created_at=datetime.utcnow()
                )

            db.add(next_q)
            db.commit()
            db.refresh(next_q)

            next_q_data = {
                "id": next_q.id,
                "question_index": next_q.question_index,
                "question_text": next_q.question_text,
                "difficulty": next_q.difficulty,
                "question_type": next_q.question_type,
                "ideal_concept_points": next_q.ideal_concept_points_json
            }

        db.commit()

        return {
            "session_id": session.id,
            "question_id": question.id,
            "evaluation": {
                "id": evaluation.id,
                "score": evaluation.score,
                "correctness": evaluation.correctness,
                "relevance": evaluation.relevance,
                "completeness": evaluation.completeness,
                "conceptual_understanding": evaluation.conceptual_understanding,
                "feedback": evaluation.feedback,
                "key_strengths": evaluation.key_strengths_json,
                "missing_points": evaluation.missing_points_json,
                "suggested_follow_up_topic": evaluation.suggested_follow_up_topic
            },
            "has_next_question": has_next,
            "next_question": next_q_data,
            "is_session_complete": not has_next
        }

    def end_session(self, db: Session, session_id: int, user_id: int) -> Dict[str, Any]:
        """
        Finalizes viva session, aggregates dimensional scores, generates qualitative report,
        and synchronizes performance with Learner Model and SM-2 revision scheduler.
        """
        session = db.query(VivaSession).filter(
            VivaSession.id == session_id,
            VivaSession.user_id == user_id
        ).first()
        if not session:
            raise ValueError("Viva session not found.")

        evaluations = db.query(VivaEvaluation).filter(VivaEvaluation.session_id == session.id).all()
        
        if evaluations:
            avg_score = round(sum(e.score for e in evaluations) / len(evaluations), 1)
            avg_corr = round(sum(e.correctness for e in evaluations) / len(evaluations), 1)
            avg_rel = round(sum(e.relevance for e in evaluations) / len(evaluations), 1)
            avg_comp = round(sum(e.completeness for e in evaluations) / len(evaluations), 1)
            avg_conc = round(sum(e.conceptual_understanding for e in evaluations) / len(evaluations), 1)
        else:
            avg_score = avg_corr = avg_rel = avg_comp = avg_conc = 0.0

        # Build transcript history for AI report generator
        qa_history = []
        questions = db.query(VivaQuestion).filter(VivaQuestion.session_id == session.id).order_by(VivaQuestion.question_index.asc()).all()
        for q in questions:
            ans = db.query(VivaAnswer).filter(VivaAnswer.question_id == q.id).first()
            ev = db.query(VivaEvaluation).filter(VivaEvaluation.question_id == q.id).first()
            qa_history.append({
                "question_text": q.question_text,
                "answer_text": ans.answer_text if ans else "",
                "evaluation": {
                    "score": ev.score if ev else 0,
                    "correctness": ev.correctness if ev else 0,
                    "feedback": ev.feedback if ev else ""
                }
            })

        # Generate Comprehensive Report
        report = ai_service.generate_viva_final_report(
            topic=session.topic,
            mode=session.mode,
            overall_score=avg_score,
            qa_history=qa_history
        )

        was_already_completed = (session.status == "completed")

        now = datetime.utcnow()
        session.status = "completed"
        session.completed_at = now
        session.overall_score = avg_score
        session.correctness_score = avg_corr
        session.relevance_score = avg_rel
        session.completeness_score = avg_comp
        session.conceptual_score = avg_conc
        session.strengths_json = report.get("strengths", [])
        session.weak_areas_json = report.get("weak_areas", [])
        session.suggested_improvements_json = report.get("suggested_improvements", [])
        session.overall_feedback = report.get("overall_feedback", "")

        db.commit()
        db.refresh(session)

        # Update Learner Model & Spaced Repetition
        duration_est = max(5, len(evaluations) * 3)  # Approx 3 minutes per question
        learner_service.update_topic_after_viva(
            db=db,
            user_id=user_id,
            topic_name=session.topic,
            score=avg_score,
            duration_minutes=duration_est
        )

        # Also trigger SM-2 revision schedule update
        if avg_score >= 90.0:
            quality = 5
        elif avg_score >= 75.0:
            quality = 4
        elif avg_score >= 55.0:
            quality = 3
        elif avg_score >= 35.0:
            quality = 2
        elif avg_score > 0:
            quality = 1
        else:
            quality = 0

        revision_service.record_topic_revision(
            db=db,
            user_id=user_id,
            topic_name=session.topic,
            quality=quality,
            material_id=session.material_id
        )

        # Create persistent Notification for Viva evaluation (with duplicate prevention)
        if not was_already_completed:
            notif = Notification(
                user_id=user_id,
                title="AI Viva Completed",
                message=f"{session.topic} ({session.mode.capitalize()}): Scored {round(avg_score, 1)}%. Final report & diagnostic feedback ready.",
                type="viva",
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.add(notif)
            db.commit()

        return self.get_session_detail(db, session.id, user_id)

    def get_session_detail(self, db: Session, session_id: int, user_id: int) -> Dict[str, Any]:
        """Retrieves full viva session detail with complete question-answer-evaluation transcript."""
        session = db.query(VivaSession).filter(
            VivaSession.id == session_id,
            VivaSession.user_id == user_id
        ).first()
        if not session:
            raise ValueError("Viva session not found.")

        questions = (
            db.query(VivaQuestion)
            .filter(VivaQuestion.session_id == session.id)
            .order_by(VivaQuestion.question_index.asc())
            .all()
        )

        transcript = []
        completed_count = 0
        for q in questions:
            ans = db.query(VivaAnswer).filter(VivaAnswer.question_id == q.id).first()
            ev = db.query(VivaEvaluation).filter(VivaEvaluation.question_id == q.id).first()
            
            ev_dict = None
            if ev:
                completed_count += 1
                ev_dict = {
                    "id": ev.id,
                    "score": ev.score,
                    "correctness": ev.correctness,
                    "relevance": ev.relevance,
                    "completeness": ev.completeness,
                    "conceptual_understanding": ev.conceptual_understanding,
                    "feedback": ev.feedback,
                    "key_strengths": ev.key_strengths_json,
                    "missing_points": ev.missing_points_json,
                    "suggested_follow_up_topic": ev.suggested_follow_up_topic
                }

            transcript.append({
                "question_id": q.id,
                "question_index": q.question_index,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "difficulty": q.difficulty,
                "ideal_concept_points": q.ideal_concept_points_json,
                "answer_text": ans.answer_text if ans else None,
                "evaluation": ev_dict
            })

        return {
            "id": session.id,
            "topic": session.topic,
            "material_id": session.material_id,
            "mode": session.mode,
            "difficulty": session.difficulty,
            "status": session.status,
            "total_questions": session.total_questions,
            "completed_questions": completed_count,
            "overall_score": session.overall_score,
            "correctness_score": session.correctness_score,
            "relevance_score": session.relevance_score,
            "completeness_score": session.completeness_score,
            "conceptual_score": session.conceptual_score,
            "strengths": session.strengths_json or [],
            "weak_areas": session.weak_areas_json or [],
            "suggested_improvements": session.suggested_improvements_json or [],
            "overall_feedback": session.overall_feedback,
            "created_at": session.created_at,
            "completed_at": session.completed_at,
            "transcript": transcript
        }

    def get_user_history(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Retrieves user's past viva sessions history."""
        sessions = (
            db.query(VivaSession)
            .filter(VivaSession.user_id == user_id)
            .order_by(VivaSession.created_at.desc())
            .all()
        )

        completed = [s for s in sessions if s.status == "completed"]
        avg_score = round(sum(s.overall_score for s in completed) / len(completed), 1) if completed else 0.0

        return {
            "total_sessions": len(sessions),
            "average_score": avg_score,
            "sessions": [
                {
                    "id": s.id,
                    "topic": s.topic,
                    "material_id": s.material_id,
                    "mode": s.mode,
                    "difficulty": s.difficulty,
                    "status": s.status,
                    "total_questions": s.total_questions,
                    "overall_score": s.overall_score,
                    "created_at": s.created_at,
                    "completed_at": s.completed_at
                }
                for s in sessions
            ]
        }


viva_service = VivaService()
