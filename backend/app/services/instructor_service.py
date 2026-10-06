import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.user import User, Role, Profile
from app.models.learner import LearnerModel, Progress
from app.models.study import QuizAttempt, Performance, Notification
from app.models.viva import VivaSession
from app.models.assessment import Assessment, AssessmentAssignment, AssessmentSubmission, InstructorFeedback
from app.models.subject import Subject, Topic
from app.schemas.instructor import (
    AssessmentCreateRequest,
    AssessmentUpdateRequest,
    AssignAssessmentRequest,
    CreateFeedbackRequest,
    StudentSummaryItem,
    StudentTopicMasteryItem,
    StudentDetailResponse,
    TopicAnalyticsItem,
    ClassAnalyticsOverview,
    ClassSummaryReport
)

logger = logging.getLogger("uvicorn.error")

class InstructorService:

    def get_dashboard_summary(self, db: Session, instructor_id: int) -> Dict[str, Any]:
        """
        Gathers high-level summary KPIs for the Instructor Dashboard.
        """
        # 1. Total Students
        student_role = db.query(Role).filter(Role.name == "student").first()
        student_role_id = student_role.id if student_role else None
        
        students_query = db.query(User).filter(User.role_id == student_role_id) if student_role_id else db.query(User).filter(User.email != "instructor@study.edu", User.email != "admin@study.edu")
        total_students = students_query.count()

        # 2. Total Assessments & Assignments
        total_assessments = db.query(Assessment).filter(Assessment.instructor_id == instructor_id).count()
        total_assignments = db.query(AssessmentAssignment).filter(AssessmentAssignment.instructor_id == instructor_id).count()

        # 3. Submissions
        submissions = db.query(AssessmentSubmission).join(Assessment).filter(Assessment.instructor_id == instructor_id).all()
        total_submissions = len(submissions)
        avg_assessment_score = (sum(s.percentage for s in submissions) / total_submissions) if total_submissions > 0 else 0.0

        # 4. Class Mastery
        learners = db.query(LearnerModel).all()
        avg_class_mastery = (sum(l.mastery for l in learners) / len(learners)) if learners else 70.0

        # 5. At-Risk / Excelling counts
        students = students_query.all()
        at_risk_count = 0
        excelling_count = 0

        for s in students:
            s_learners = [l for l in learners if l.user_id == s.id]
            if s_learners:
                s_avg = sum(l.mastery for l in s_learners) / len(s_learners)
            else:
                s_avg = 50.0
            if s_avg < 55.0:
                at_risk_count += 1
            elif s_avg >= 80.0:
                excelling_count += 1

        # 6. Recent Submissions
        recent_submissions = (
            db.query(AssessmentSubmission)
            .join(Assessment)
            .filter(Assessment.instructor_id == instructor_id)
            .order_by(desc(AssessmentSubmission.submitted_at))
            .limit(5)
            .all()
        )
        recent_submissions_data = []
        for sub in recent_submissions:
            student_user = db.query(User).filter(User.id == sub.student_id).first()
            s_name = student_user.profile.full_name if (student_user and student_user.profile) else (student_user.email if student_user else f"Student #{sub.student_id}")
            recent_submissions_data.append({
                "id": sub.id,
                "assessment_id": sub.assessment_id,
                "assessment_title": sub.assessment.title if sub.assessment else "Assessment",
                "student_id": sub.student_id,
                "student_name": s_name,
                "score": sub.score,
                "total_points": sub.total_points,
                "percentage": sub.percentage,
                "passed": sub.passed,
                "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None
            })

        # 7. Recent Feedback
        recent_feedbacks = (
            db.query(InstructorFeedback)
            .filter(InstructorFeedback.instructor_id == instructor_id)
            .order_by(desc(InstructorFeedback.created_at))
            .limit(5)
            .all()
        )
        recent_feedbacks_data = []
        for fb in recent_feedbacks:
            s_user = db.query(User).filter(User.id == fb.student_id).first()
            s_name = s_user.profile.full_name if (s_user and s_user.profile) else (s_user.email if s_user else f"Student #{fb.student_id}")
            recent_feedbacks_data.append({
                "id": fb.id,
                "student_id": fb.student_id,
                "student_name": s_name,
                "topic": fb.topic,
                "feedback_type": fb.feedback_type,
                "feedback_text": fb.feedback_text[:120] + "..." if len(fb.feedback_text) > 120 else fb.feedback_text,
                "created_at": fb.created_at.isoformat() if fb.created_at else None
            })

        return {
            "total_students": total_students,
            "total_assessments": total_assessments,
            "total_assignments": total_assignments,
            "total_submissions": total_submissions,
            "average_assessment_score": round(avg_assessment_score, 1),
            "average_class_mastery": round(avg_class_mastery, 1),
            "at_risk_students_count": at_risk_count,
            "excelling_students_count": excelling_count,
            "recent_submissions": recent_submissions_data,
            "recent_feedbacks": recent_feedbacks_data
        }

    def list_students(self, db: Session) -> List[StudentSummaryItem]:
        """
        Retrieves all students with their aggregated mastery and performance statistics.
        """
        student_role = db.query(Role).filter(Role.name == "student").first()
        if student_role:
            students = db.query(User).filter(User.role_id == student_role.id).all()
        else:
            students = db.query(User).filter(User.email != "instructor@study.edu", User.email != "admin@study.edu").all()

        results = []
        for s in students:
            # Name & Profile
            name = s.profile.full_name if s.profile else s.email.split("@")[0]
            joined = s.created_at.strftime("%B %Y") if s.created_at else "September 2026"
            avatar = s.profile.avatar_url if s.profile else None

            # Learner models
            learners = db.query(LearnerModel).filter(LearnerModel.user_id == s.id).all()
            topics_tracked = len(learners)
            overall_mastery = (sum(l.mastery for l in learners) / topics_tracked) if topics_tracked > 0 else 50.0

            # Quizzes
            attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == s.id, QuizAttempt.status == "completed").all()
            quizzes_completed = len(attempts)
            avg_quiz = (sum(a.accuracy for a in attempts) / quizzes_completed) if quizzes_completed > 0 else 0.0

            # Vivas
            vivas = db.query(VivaSession).filter(VivaSession.user_id == s.id, VivaSession.status == "completed").all()
            vivas_completed = len(vivas)
            avg_viva = (sum(v.overall_score for v in vivas) / vivas_completed) if vivas_completed > 0 else 0.0

            # Feedbacks count
            fb_count = db.query(InstructorFeedback).filter(InstructorFeedback.student_id == s.id).count()

            # Risk status
            if overall_mastery >= 80.0 and (quizzes_completed > 0 or vivas_completed > 0):
                risk = "excelling"
            elif overall_mastery < 55.0:
                risk = "at_risk"
            else:
                risk = "on_track"

            # Last activity
            last_quiz = db.query(func.max(QuizAttempt.created_at)).filter(QuizAttempt.user_id == s.id).scalar()
            last_viva = db.query(func.max(VivaSession.created_at)).filter(VivaSession.user_id == s.id).scalar()
            last_active = max(filter(None, [last_quiz, last_viva, s.created_at]), default=datetime.utcnow())

            results.append(StudentSummaryItem(
                id=s.id,
                name=name,
                email=s.email,
                avatar_url=avatar,
                joined_date=joined,
                overall_mastery=round(overall_mastery, 1),
                topics_tracked=topics_tracked,
                quizzes_completed=quizzes_completed,
                average_quiz_score=round(avg_quiz, 1),
                viva_sessions_completed=vivas_completed,
                average_viva_score=round(avg_viva, 1),
                risk_status=risk,
                last_active=last_active,
                feedbacks_count=fb_count
            ))

        return results

    def get_student_detail(self, db: Session, student_id: int) -> Optional[StudentDetailResponse]:
        """
        Retrieves detailed progress, topic mastery, quizzes, vivas, and feedback history for a student.
        """
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            return None

        name = student.profile.full_name if student.profile else student.email.split("@")[0]
        bio = student.profile.bio if student.profile else None
        avatar = student.profile.avatar_url if student.profile else None
        joined = student.created_at.strftime("%B %Y") if student.created_at else "September 2026"

        # Topics
        learners = db.query(LearnerModel).filter(LearnerModel.user_id == student_id).all()
        topic_items = []
        for l in learners:
            if l.mastery >= 80:
                status = "mastered"
            elif l.mastery >= 60:
                status = "proficient"
            else:
                status = "needs_practice"
            topic_items.append(StudentTopicMasteryItem(
                topic=l.topic,
                mastery=round(l.mastery, 1),
                quiz_accuracy=round(l.quiz_accuracy, 1),
                flashcard_score=round(l.flashcard_performance, 1),
                viva_score=round(l.viva_performance, 1),
                recall_probability=round(l.recall_reliability, 2),
                last_reviewed=l.last_reviewed,
                status=status
            ))

        overall_mastery = (sum(l.mastery for l in learners) / len(learners)) if learners else 50.0

        # Progress / study time
        progress = db.query(Progress).filter(Progress.user_id == student_id).first()
        total_mins = progress.total_study_time_minutes if progress else 0
        streak = progress.current_streak_days if progress else 0

        # Quizzes
        quizzes = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == student_id)
            .order_by(desc(QuizAttempt.created_at))
            .limit(10)
            .all()
        )
        recent_quizzes = [{
            "id": q.id,
            "topic": q.topic,
            "difficulty": q.difficulty,
            "score": q.score,
            "total_questions": q.total_questions,
            "accuracy": q.accuracy,
            "status": q.status,
            "created_at": q.created_at.isoformat() if q.created_at else None
        } for q in quizzes]

        # Vivas
        vivas = (
            db.query(VivaSession)
            .filter(VivaSession.user_id == student_id)
            .order_by(desc(VivaSession.created_at))
            .limit(10)
            .all()
        )
        recent_vivas = [{
            "id": v.id,
            "topic": v.topic,
            "mode": v.mode,
            "status": v.status,
            "overall_score": v.overall_score,
            "rating": v.performance_rating,
            "created_at": v.created_at.isoformat() if v.created_at else None
        } for v in vivas]

        # Submissions
        subs = (
            db.query(AssessmentSubmission)
            .filter(AssessmentSubmission.student_id == student_id)
            .order_by(desc(AssessmentSubmission.submitted_at))
            .all()
        )
        submissions_data = [{
            "id": sub.id,
            "assessment_id": sub.assessment_id,
            "assessment_title": sub.assessment.title if sub.assessment else "Assessment",
            "score": sub.score,
            "total_points": sub.total_points,
            "percentage": sub.percentage,
            "passed": sub.passed,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None
        } for sub in subs]

        # Feedbacks
        fbs = (
            db.query(InstructorFeedback)
            .filter(InstructorFeedback.student_id == student_id)
            .order_by(desc(InstructorFeedback.created_at))
            .all()
        )
        feedbacks_data = [{
            "id": fb.id,
            "instructor_id": fb.instructor_id,
            "instructor_name": fb.instructor.profile.full_name if (fb.instructor and fb.instructor.profile) else "Instructor",
            "topic": fb.topic,
            "feedback_type": fb.feedback_type,
            "feedback_text": fb.feedback_text,
            "action_items": fb.action_items_json,
            "created_at": fb.created_at.isoformat() if fb.created_at else None
        } for fb in fbs]

        # Risk status
        if overall_mastery >= 80.0:
            risk = "excelling"
        elif overall_mastery < 55.0:
            risk = "at_risk"
        else:
            risk = "on_track"

        return StudentDetailResponse(
            id=student.id,
            name=name,
            email=student.email,
            bio=bio,
            avatar_url=avatar,
            joined_date=joined,
            overall_mastery=round(overall_mastery, 1),
            total_study_minutes=total_mins,
            streak_days=streak,
            risk_status=risk,
            topics=topic_items,
            recent_quizzes=recent_quizzes,
            recent_vivas=recent_vivas,
            submissions=submissions_data,
            feedbacks=feedbacks_data
        )

    def create_assessment(self, db: Session, instructor_id: int, req: AssessmentCreateRequest) -> Assessment:
        """
        Creates a new Assessment record.
        """
        q_json = [q.model_dump() for q in req.questions]
        assessment = Assessment(
            instructor_id=instructor_id,
            subject_id=req.subject_id,
            title=req.title.strip(),
            description=req.description.strip() if req.description else None,
            topic=req.topic.strip(),
            difficulty=req.difficulty,
            time_limit_minutes=req.time_limit_minutes,
            total_points=req.total_points,
            pass_percentage=req.pass_percentage,
            questions_json=q_json,
            is_published=req.is_published
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    def list_assessments(self, db: Session, instructor_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Lists all assessments with submission and assignment metadata.
        """
        query = db.query(Assessment)
        if instructor_id:
            query = query.filter(Assessment.instructor_id == instructor_id)
        
        assessments = query.order_by(desc(Assessment.created_at)).all()
        results = []

        for a in assessments:
            # Submissions count and average
            subs = a.submissions or []
            sub_count = len(subs)
            avg_score = (sum(s.percentage for s in subs) / sub_count) if sub_count > 0 else 0.0

            inst_name = a.instructor.profile.full_name if (a.instructor and a.instructor.profile) else "Instructor"
            sub_name = a.subject.name if a.subject else None

            results.append({
                "id": a.id,
                "instructor_id": a.instructor_id,
                "instructor_name": inst_name,
                "subject_id": a.subject_id,
                "subject_name": sub_name,
                "title": a.title,
                "description": a.description,
                "topic": a.topic,
                "difficulty": a.difficulty,
                "time_limit_minutes": a.time_limit_minutes,
                "total_points": a.total_points,
                "pass_percentage": a.pass_percentage,
                "question_count": len(a.questions_json),
                "questions": a.questions_json,
                "is_published": a.is_published,
                "created_at": a.created_at,
                "updated_at": a.updated_at,
                "total_assignments": len(a.assignments or []),
                "total_submissions": sub_count,
                "average_score": round(avg_score, 1)
            })

        return results

    def get_assessment(self, db: Session, assessment_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single assessment with its submissions and assignments.
        """
        a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not a:
            return None

        subs = a.submissions or []
        sub_count = len(subs)
        avg_score = (sum(s.percentage for s in subs) / sub_count) if sub_count > 0 else 0.0
        inst_name = a.instructor.profile.full_name if (a.instructor and a.instructor.profile) else "Instructor"

        # Format submission details
        submissions_detail = []
        for s in subs:
            s_name = s.student.profile.full_name if (s.student and s.student.profile) else (s.student.email if s.student else "Student")
            submissions_detail.append({
                "id": s.id,
                "student_id": s.student_id,
                "student_name": s_name,
                "student_email": s.student.email if s.student else "",
                "score": s.score,
                "total_points": s.total_points,
                "percentage": s.percentage,
                "passed": s.passed,
                "time_spent_seconds": s.time_spent_seconds,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None
            })

        return {
            "id": a.id,
            "instructor_id": a.instructor_id,
            "instructor_name": inst_name,
            "subject_id": a.subject_id,
            "subject_name": a.subject.name if a.subject else None,
            "title": a.title,
            "description": a.description,
            "topic": a.topic,
            "difficulty": a.difficulty,
            "time_limit_minutes": a.time_limit_minutes,
            "total_points": a.total_points,
            "pass_percentage": a.pass_percentage,
            "question_count": len(a.questions_json),
            "questions": a.questions_json,
            "is_published": a.is_published,
            "created_at": a.created_at,
            "updated_at": a.updated_at,
            "total_assignments": len(a.assignments or []),
            "total_submissions": sub_count,
            "average_score": round(avg_score, 1),
            "submissions": submissions_detail
        }

    def update_assessment(self, db: Session, assessment_id: int, req: AssessmentUpdateRequest) -> Optional[Assessment]:
        a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not a:
            return None

        if req.title is not None:
            a.title = req.title.strip()
        if req.topic is not None:
            a.topic = req.topic.strip()
        if req.description is not None:
            a.description = req.description.strip()
        if req.difficulty is not None:
            a.difficulty = req.difficulty
        if req.time_limit_minutes is not None:
            a.time_limit_minutes = req.time_limit_minutes
        if req.total_points is not None:
            a.total_points = req.total_points
        if req.pass_percentage is not None:
            a.pass_percentage = req.pass_percentage
        if req.questions is not None:
            a.questions_json = [q.model_dump() for q in req.questions]
        if req.is_published is not None:
            a.is_published = req.is_published
        
        a.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(a)
        return a

    def delete_assessment(self, db: Session, assessment_id: int) -> bool:
        a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not a:
            return False
        db.delete(a)
        db.commit()
        return True

    def assign_assessment(self, db: Session, assessment_id: int, instructor_id: int, req: AssignAssessmentRequest) -> AssessmentAssignment:
        assignment = AssessmentAssignment(
            assessment_id=assessment_id,
            instructor_id=instructor_id,
            assigned_to_all=req.assigned_to_all,
            student_id=req.student_id if not req.assigned_to_all else None,
            due_date=req.due_date,
            instructions=req.instructions,
            status="active"
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # Notify assigned student(s)
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        title = assessment.title if assessment else "New Assessment"

        if req.assigned_to_all:
            student_role = db.query(Role).filter(Role.name == "student").first()
            if student_role:
                students = db.query(User).filter(User.role_id == student_role.id).all()
            else:
                students = db.query(User).filter(User.email != "instructor@study.edu", User.email != "admin@study.edu").all()
            for s in students:
                notif = Notification(
                    user_id=s.id,
                    title="New Assessment Assigned",
                    message=f"Your instructor assigned '{title}'. Check your assessments to complete it.",
                    type="quiz"
                )
                db.add(notif)
        elif req.student_id:
            notif = Notification(
                user_id=req.student_id,
                title="New Assessment Assigned",
                message=f"Your instructor assigned '{title}'. Check your assessments to complete it.",
                type="quiz"
            )
            db.add(notif)
        db.commit()

        return assignment

    def list_assignments(self, db: Session, instructor_id: Optional[int] = None) -> List[Dict[str, Any]]:
        query = db.query(AssessmentAssignment)
        if instructor_id:
            query = query.filter(AssessmentAssignment.instructor_id == instructor_id)
        
        assignments = query.order_by(desc(AssessmentAssignment.created_at)).all()
        results = []
        for asgn in assignments:
            s_name = asgn.student.profile.full_name if (asgn.student and asgn.student.profile) else (asgn.student.email if asgn.student else None)
            results.append({
                "id": asgn.id,
                "assessment_id": asgn.assessment_id,
                "assessment_title": asgn.assessment.title if asgn.assessment else "Assessment",
                "topic": asgn.assessment.topic if asgn.assessment else "General",
                "instructor_id": asgn.instructor_id,
                "assigned_to_all": asgn.assigned_to_all,
                "student_id": asgn.student_id,
                "student_name": s_name,
                "due_date": asgn.due_date,
                "instructions": asgn.instructions,
                "status": asgn.status,
                "created_at": asgn.created_at,
                "submissions_count": len(asgn.submissions or [])
            })
        return results

    def get_class_analytics(self, db: Session) -> ClassAnalyticsOverview:
        """
        Computes aggregate class analytics across all students and syllabus topics.
        """
        student_role = db.query(Role).filter(Role.name == "student").first()
        if student_role:
            students = db.query(User).filter(User.role_id == student_role.id).all()
        else:
            students = db.query(User).filter(User.email != "instructor@study.edu", User.email != "admin@study.edu").all()

        total_students = len(students)
        active_7d = total_students  # Default for demo active cohort

        # Learner Model Topic Aggregations
        all_learners = db.query(LearnerModel).all()
        topics_dict: Dict[str, List[LearnerModel]] = {}
        for l in all_learners:
            if l.topic not in topics_dict:
                topics_dict[l.topic] = []
            topics_dict[l.topic].append(l)

        topic_items = []
        for topic_name, topic_records in topics_dict.items():
            count = len(topic_records)
            avg_m = sum(r.mastery for r in topic_records) / count if count > 0 else 0.0
            mastered = sum(1 for r in topic_records if r.mastery >= 80.0)
            at_risk = sum(1 for r in topic_records if r.mastery < 55.0)
            avg_quiz = sum(r.quiz_accuracy for r in topic_records) / count if count > 0 else 0.0
            avg_viva = sum(r.viva_performance for r in topic_records) / count if count > 0 else 0.0

            # Weakness summary
            if avg_m < 60.0:
                weakness = f"Class struggling with core mechanics and boundary conditions in {topic_name}."
            elif avg_m < 75.0:
                weakness = f"Moderate grasp. Needs practice on complex edge cases and optimization."
            else:
                weakness = f"Strong class-wide mastery. Foundation and application well understood."

            topic_items.append(TopicAnalyticsItem(
                topic=topic_name,
                subject_name=None,
                average_mastery=round(avg_m, 1),
                students_count=count,
                mastered_count=mastered,
                at_risk_count=at_risk,
                average_quiz_accuracy=round(avg_quiz, 1),
                average_viva_score=round(avg_viva, 1),
                common_weakness_summary=weakness
            ))

        topic_items.sort(key=lambda x: x.average_mastery)

        # Assessments & Submissions
        assessments_count = db.query(Assessment).count()
        submissions = db.query(AssessmentSubmission).all()
        subs_count = len(submissions)
        avg_sub_score = (sum(s.percentage for s in submissions) / subs_count) if subs_count > 0 else 0.0

        # Quizzes & Vivas
        total_quizzes = db.query(QuizAttempt).filter(QuizAttempt.status == "completed").count()
        total_vivas = db.query(VivaSession).filter(VivaSession.status == "completed").count()

        # Study hours
        progress_records = db.query(Progress).all()
        total_minutes = sum(p.total_study_time_minutes for p in progress_records)
        total_hours = round(total_minutes / 60.0, 1)

        # Average class mastery
        avg_class_m = (sum(l.mastery for l in all_learners) / len(all_learners)) if all_learners else 70.0

        # Score distributions
        score_dist = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "Below 60": 0}
        for s in submissions:
            pct = s.percentage
            if pct >= 90:
                score_dist["90-100"] += 1
            elif pct >= 80:
                score_dist["80-89"] += 1
            elif pct >= 70:
                score_dist["70-79"] += 1
            elif pct >= 60:
                score_dist["60-69"] += 1
            else:
                score_dist["Below 60"] += 1

        # Student risk categorization
        excelling_count = sum(1 for s in students if (sum(l.mastery for l in all_learners if l.user_id == s.id) / max(1, sum(1 for l in all_learners if l.user_id == s.id))) >= 80.0)
        at_risk_count = sum(1 for s in students if (sum(l.mastery for l in all_learners if l.user_id == s.id) / max(1, sum(1 for l in all_learners if l.user_id == s.id))) < 55.0)

        return ClassAnalyticsOverview(
            total_students=total_students,
            active_students_7d=active_7d,
            average_class_mastery=round(avg_class_m, 1),
            at_risk_students_count=at_risk_count,
            excelling_students_count=excelling_count,
            total_assessments_created=assessments_count,
            total_submissions_received=subs_count,
            average_assessment_score=round(avg_sub_score, 1),
            class_quizzes_completed=total_quizzes,
            class_vivas_completed=total_vivas,
            total_study_hours=total_hours,
            topic_distribution=topic_items,
            score_distribution=score_dist
        )

    def create_feedback(self, db: Session, instructor_id: int, req: CreateFeedbackRequest) -> InstructorFeedback:
        feedback = InstructorFeedback(
            instructor_id=instructor_id,
            student_id=req.student_id,
            assessment_id=req.assessment_id,
            submission_id=req.submission_id,
            topic=req.topic,
            feedback_type=req.feedback_type,
            feedback_text=req.feedback_text.strip(),
            action_items_json=req.action_items or []
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        # Notify student
        topic_suffix = f" on '{req.topic}'" if req.topic else ""
        notif = Notification(
            user_id=req.student_id,
            title="Instructor Feedback Received",
            message=f"Your instructor posted personalized feedback{topic_suffix}: {req.feedback_text[:100]}...",
            type="info"
        )
        db.add(notif)
        db.commit()

        return feedback

    def list_feedbacks(
        self,
        db: Session,
        instructor_id: Optional[int] = None,
        student_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query = db.query(InstructorFeedback)
        if instructor_id:
            query = query.filter(InstructorFeedback.instructor_id == instructor_id)
        if student_id:
            query = query.filter(InstructorFeedback.student_id == student_id)
        
        feedbacks = query.order_by(desc(InstructorFeedback.created_at)).all()
        results = []
        for fb in feedbacks:
            inst_name = fb.instructor.profile.full_name if (fb.instructor and fb.instructor.profile) else "Instructor"
            stud_name = fb.student.profile.full_name if (fb.student and fb.student.profile) else (fb.student.email if fb.student else "Student")
            results.append({
                "id": fb.id,
                "instructor_id": fb.instructor_id,
                "instructor_name": inst_name,
                "student_id": fb.student_id,
                "student_name": stud_name,
                "student_email": fb.student.email if fb.student else "",
                "assessment_id": fb.assessment_id,
                "assessment_title": fb.assessment.title if fb.assessment else None,
                "topic": fb.topic,
                "feedback_type": fb.feedback_type,
                "feedback_text": fb.feedback_text,
                "action_items": fb.action_items_json or [],
                "is_read": fb.is_read,
                "created_at": fb.created_at
            })
        return results

    def generate_class_report(self, db: Session, instructor_name: str) -> ClassSummaryReport:
        """
        Synthesizes a comprehensive printable/exportable class performance report.
        """
        analytics = self.get_class_analytics(db)
        students = self.list_students(db)

        # Top performers
        sorted_students = sorted(students, key=lambda x: x.overall_mastery, reverse=True)
        top_performers = [{
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "mastery": s.overall_mastery,
            "quizzes": s.quizzes_completed,
            "vivas": s.viva_sessions_completed
        } for s in sorted_students[:3]]

        # Students needing intervention
        at_risk_students = [{
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "mastery": s.overall_mastery,
            "risk_status": s.risk_status,
            "quizzes": s.quizzes_completed,
            "vivas": s.viva_sessions_completed
        } for s in sorted_students if s.risk_status == "at_risk"]

        # Pedagogical recommended actions
        recommended_actions = []
        if analytics.topic_distribution:
            weakest_topic = analytics.topic_distribution[0].topic
            recommended_actions.append(f"Conduct a targeted recitation or live problem walkthrough for '{weakest_topic}'.")
            if len(analytics.topic_distribution) > 1:
                second_weakest = analytics.topic_distribution[1].topic
                recommended_actions.append(f"Assign supplementary active recall flashcard sets and mini-quizzes on '{second_weakest}'.")

        recommended_actions.extend([
            "Issue personalized intervention feedback to students in the At-Risk tier.",
            "Schedule a mid-semester technical viva review for students with viva scores under 60%."
        ])

        return ClassSummaryReport(
            generated_at=datetime.utcnow(),
            instructor_name=instructor_name,
            total_enrolled=analytics.total_students,
            class_average_mastery=analytics.average_class_mastery,
            assessment_summary={
                "total_created": analytics.total_assessments_created,
                "total_submissions": analytics.total_submissions_received,
                "average_score": analytics.average_assessment_score,
                "score_distribution": analytics.score_distribution
            },
            topic_breakdown=analytics.topic_distribution,
            top_performers=top_performers,
            students_needing_intervention=at_risk_students,
            recommended_class_actions=recommended_actions
        )

instructor_service = InstructorService()
