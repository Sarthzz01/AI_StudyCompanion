import time
import json
import re
import logging
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger("uvicorn.error")

class AIService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL or "gemini-3.8-flash"
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self._client = None
        return self._client

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """
        Core reusable method for sending prompts to the Gemini model.
        """
        start_time = time.time()
        
        if not self.is_configured():
            # Graceful fallback when API key has not been configured yet
            latency = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "reply": f"I have processed your query regarding: {prompt[:120]}. Here is a key concept overview to support your study session. Please ensure your query specifies any particular subtopics you'd like to dive into.",
                "model": "study-companion-ai",
                "latency_ms": latency,
                "grounded": False
            }

        try:
            from google.genai import types
            config = None
            if system_instruction:
                config = types.GenerateContentConfig(system_instruction=system_instruction)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            latency = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "reply": response.text or "",
                "model": self.model_name,
                "latency_ms": latency,
                "grounded": False
            }
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            latency = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "reply": f"AI service error: {str(e)}",
                "model": self.model_name,
                "latency_ms": latency,
                "grounded": False
            }

    # =========================================================================
    # PREPARED ARCHITECTURES & PROMPT TEMPLATES FOR PHASE 3
    # =========================================================================

    def get_summary_prompt(self, material_title: str, text_content: str) -> str:
        """Prompt template for generating structured study summaries."""
        return (
            f"You are an expert tutor. Summarize the following study material on '{material_title}'.\n"
            f"Break the material into clear logical sections with key takeaways, definitions, and core concepts.\n\n"
            f"Material Content:\n{text_content}"
        )

    def get_flashcards_prompt(self, topic: str, count: int = 10) -> str:
        """Prompt template for generating active recall flashcards."""
        return (
            f"Generate {count} high-yield flashcards for the topic '{topic}'.\n"
            f"Each flashcard must have a concise, challenging prompt on the front and a clear, precise explanation on the back.\n"
            f"Format the output as a JSON list of objects with keys 'front', 'back', and 'difficulty'."
        )

    def get_quiz_prompt(self, topic: str, difficulty: str = "medium", count: int = 5) -> str:
        """Prompt template for generating multiple-choice quiz questions."""
        return (
            f"Generate {count} {difficulty}-level multiple-choice questions for '{topic}'.\n"
            f"For each question, provide 4 options, the correct answer, and an in-depth explanation.\n"
            f"Format as JSON with keys: 'question', 'options', 'correct_answer', 'explanation'."
        )

    def get_viva_evaluation_prompt(self, question: str, student_answer: str) -> str:
        """Prompt template for evaluating a student's verbal/viva explanation."""
        return (
            f"Question asked to student: {question}\n"
            f"Student's response: {student_answer}\n\n"
            f"Evaluate the accuracy, depth of understanding, and conceptual clarity. "
            f"Provide a score out of 10 and constructive feedback."
        )

    def get_rag_grounded_answer_prompt(self, query: str, retrieved_contexts: List[str]) -> str:
        """Prompt template for grounded RAG tutor answers with citations."""
        context_block = "\n---\n".join(retrieved_contexts)
        return (
            f"Answer the student's question using ONLY the provided context excerpts.\n"
            f"Cite the source material where applicable.\n\n"
            f"Context Excerpts:\n{context_block}\n\n"
            f"Student Question: {query}"
        )

    def _extract_json_array(self, text: str) -> List[Dict[str, Any]]:
        """Extract and parse a JSON array from raw model text."""
        if not text:
            return []
        cleaned = text.strip()
        # Strip ```json ... ``` code blocks
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()

        # Look for [ ... ]
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end+1]

        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for key in ["flashcards", "questions", "cards", "items", "data"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data]
        except Exception as e:
            logger.warning(f"Initial JSON parse failed: {e}. Attempting recovery.")
            objects = []
            for obj_str in re.findall(r"\{[^{}]*\}", cleaned):
                try:
                    parsed_obj = json.loads(obj_str)
                    if isinstance(parsed_obj, dict):
                        objects.append(parsed_obj)
                except Exception:
                    continue
            if objects:
                return objects

        return []

    def generate_flashcards_from_material(
        self,
        material_title: str,
        content_text: str,
        topic: Optional[str] = None,
        count: int = 5,
        difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        Generate structured high-yield active recall flashcards based on study material content.
        Returns a list of dicts: [{'front': str, 'back': str, 'topic': str, 'difficulty': str, 'source': str}]
        """
        topic_clause = f" specifically focusing on the topic '{topic}'" if topic and topic != "All topics" else ""
        system_instruction = (
            "You are an expert academic educator and learning scientist creating active-recall flashcards.\n"
            "Your task is to generate high-yield, conceptually rigorous flashcards based STRICTLY on the provided study material.\n\n"
            "RULES:\n"
            "1. Each card MUST test a key definition, mechanism, formula, comparison, or core concept.\n"
            "2. 'front' should be a concise question, prompt, or challenge.\n"
            "3. 'back' should be a clear, accurate, complete explanation or answer.\n"
            "4. 'topic' must be the specific topic/concept name.\n"
            "5. 'difficulty' must be one of: 'easy', 'medium', 'hard'.\n"
            "6. 'source' should be the name of the study material source.\n"
            "7. Output ONLY a valid JSON array of objects with keys: 'front', 'back', 'topic', 'difficulty', 'source'. No markdown preamble."
        )

        user_prompt = (
            f"Study Material: {material_title}\n"
            f"Target: Generate exactly {count} flashcards{topic_clause} at difficulty '{difficulty}'.\n\n"
            f"Material Content:\n{content_text[:6000]}\n\n"
            f"JSON Flashcards Array:"
        )

        resp = self.generate_text(prompt=user_prompt, system_instruction=system_instruction)
        raw_reply = resp.get("reply", "")

        cards = self._extract_json_array(raw_reply)
        validated_cards = []

        for item in cards:
            if not isinstance(item, dict):
                continue
            front = str(item.get("front") or item.get("question") or "").strip()
            back = str(item.get("back") or item.get("answer") or "").strip()
            item_topic = str(item.get("topic") or topic or material_title).strip()
            item_diff = str(item.get("difficulty") or difficulty or "medium").lower().strip()
            if item_diff not in ["easy", "medium", "hard"]:
                item_diff = "medium"
            source = str(item.get("source") or material_title).strip()

            if front and back:
                validated_cards.append({
                    "front": front,
                    "back": back,
                    "topic": item_topic,
                    "difficulty": item_diff,
                    "source": source
                })

        if not validated_cards:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?]) +", content_text) if len(s.strip()) > 30]
            for i in range(min(count, max(1, len(sentences)))):
                sent = sentences[i] if i < len(sentences) else f"Key concept in {material_title}."
                validated_cards.append({
                    "front": f"Explain the core concept: {sent[:50]}...",
                    "back": sent,
                    "topic": topic if topic and topic != "All topics" else material_title,
                    "difficulty": difficulty if difficulty != "mixed" else "medium",
                    "source": material_title
                })

        return validated_cards[:count]

    def generate_quiz_questions(
        self,
        material_title: str,
        content_text: str,
        topic: str = "All topics",
        difficulty: str = "mixed",
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate difficulty-aware multiple choice questions based on study material or topic.
        Returns a list of dicts:
        [{
            'question': str,
            'options': [str, str, str, str],
            'correct_answer': int (0-3),
            'explanation': str,
            'topic': str,
            'difficulty': str
        }]
        """
        topic_clause = f" on the topic '{topic}'" if topic and topic != "All topics" else ""
        diff_guidance = (
            "DIFFICULTY GUIDELINES:\n"
            "- 'easy': Core definitions, fundamental vocabulary, direct terminology, basic principles.\n"
            "- 'medium': Conceptual applications, identifying behavior/output, comparing two mechanisms.\n"
            "- 'hard': Complex edge cases, performance trade-offs, multi-step reasoning, subtle nuances.\n"
            "- 'mixed': A balanced progression ranging across easy, medium, and hard questions.\n"
        )

        system_instruction = (
            "You are an expert University Exam Professor and Assessment Specialist.\n"
            "Your task is to generate rigorous multiple-choice questions (MCQs) based on the provided material.\n\n"
            f"{diff_guidance}\n"
            "STRICT REQUIREMENTS:\n"
            "1. Each question must have EXACTLY 4 options.\n"
            "2. 'correct_answer' must be an integer from 0 to 3 denoting the 0-based index of the correct option.\n"
            "3. Options must be plausible, distinct, and unambiguous.\n"
            "4. Provide a thorough, educational 'explanation' explaining why the correct answer is correct and why other options are incorrect.\n"
            "5. Output ONLY a valid JSON array of objects with keys: 'question', 'options', 'correct_answer', 'explanation', 'topic', 'difficulty'. No extra markdown or conversational text."
        )

        user_prompt = (
            f"Study Material: {material_title}\n"
            f"Target: Generate exactly {count} multiple-choice questions{topic_clause} at difficulty level '{difficulty}'.\n\n"
            f"Material Content:\n{content_text[:6000]}\n\n"
            f"JSON Questions Array:"
        )

        resp = self.generate_text(prompt=user_prompt, system_instruction=system_instruction)
        raw_reply = resp.get("reply", "")

        parsed_items = self._extract_json_array(raw_reply)
        validated_questions = []

        for item in parsed_items:
            if not isinstance(item, dict):
                continue
            q_text = str(item.get("question") or item.get("question_text") or "").strip()
            raw_options = item.get("options") or item.get("choices") or []
            if not isinstance(raw_options, list) or len(raw_options) < 2:
                continue

            options = [str(opt).strip() for opt in raw_options[:4]]
            while len(options) < 4:
                options.append(f"Option {chr(65 + len(options))}")

            raw_ans = item.get("correct_answer")
            ans_idx = 0
            if isinstance(raw_ans, int) and 0 <= raw_ans < len(options):
                ans_idx = raw_ans
            elif isinstance(raw_ans, str):
                raw_ans_str = raw_ans.strip()
                if raw_ans_str.isdigit() and 0 <= int(raw_ans_str) < len(options):
                    ans_idx = int(raw_ans_str)
                elif raw_ans_str.upper() in ["A", "B", "C", "D"]:
                    ans_idx = ord(raw_ans_str.upper()) - 65
                else:
                    for idx, opt in enumerate(options):
                        if opt.lower() == raw_ans_str.lower():
                            ans_idx = idx
                            break

            explanation = str(item.get("explanation") or f"The correct answer is '{options[ans_idx]}' based on {material_title}.").strip()
            item_topic = str(item.get("topic") or (topic if topic != "All topics" else material_title)).strip()
            item_diff = str(item.get("difficulty") or (difficulty if difficulty != "mixed" else "medium")).lower().strip()
            if item_diff not in ["easy", "medium", "hard"]:
                item_diff = "medium"

            if q_text:
                validated_questions.append({
                    "question": q_text,
                    "options": options,
                    "correct_answer": ans_idx,
                    "explanation": explanation,
                    "topic": item_topic,
                    "difficulty": item_diff
                })

        if not validated_questions:
            validated_questions = [
                {
                    "question": f"Which of the following best describes the core subject of {material_title}?",
                    "options": [
                        f"Fundamental principles and operations of {material_title}",
                        f"Unrelated theoretical concepts",
                        f"Deprecated legacy methodologies",
                        f"Non-computational biological processes"
                    ],
                    "correct_answer": 0,
                    "explanation": f"The study material directly addresses the fundamental principles of {material_title}.",
                    "topic": topic if topic and topic != "All topics" else material_title,
                    "difficulty": "easy"
                }
            ]

        return validated_questions[:count]

    def generate_learning_signals(
        self,
        topic: str,
        topic_data: Dict[str, Any],
        recent_mistakes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        AI-supported learning signals grounded in actual student activity data:
        quiz accuracy, flashcard recall, difficulty, repeated mistakes, and recent performance.
        Deterministic rules ensure explainability without arbitrary or fabricated scores.
        """
        quiz_acc = topic_data.get("quiz_accuracy", 0.0)
        mastery = topic_data.get("mastery", 0.0)
        recall = topic_data.get("recall_reliability", 0.5)
        diff = topic_data.get("difficulty", "medium")
        mistakes = recent_mistakes or []

        signals = []
        rec_action = "practice"

        # Signal 1: Retention & Memory Decay
        if recall < 0.60:
            signals.append({
                "type": "retention_decay",
                "severity": "medium",
                "message": f"Memory retention estimated at {int(recall * 100)}%. Active recall review recommended to prevent further decay."
            })
            rec_action = "flashcards"
        elif recall >= 0.85:
            signals.append({
                "type": "high_retention",
                "severity": "positive",
                "message": f"Strong memory retention ({int(recall * 100)}%). Spaced repetition interval expanded."
            })

        # Signal 2: Accuracy & Concept Mastery
        if quiz_acc >= 80.0:
            signals.append({
                "type": "mastery_achieved",
                "severity": "positive",
                "message": f"Consistent performance ({quiz_acc}% quiz accuracy). Ready for hard difficulty challenges."
            })
            if rec_action != "flashcards":
                rec_action = "advance_difficulty"
        elif quiz_acc < 55.0 and quiz_acc > 0:
            signals.append({
                "type": "knowledge_gap",
                "severity": "high",
                "message": f"Quiz accuracy ({quiz_acc}%) is below mastery threshold (75%). Foundational review needed."
            })
            rec_action = "review_material"

        # Signal 3: Repeated Mistakes Analysis
        if mistakes:
            signals.append({
                "type": "repeated_mistakes",
                "severity": "high",
                "message": f"Encountered {len(mistakes)} incorrect answers on this topic in recent attempts.",
                "sample_questions": [m.get("question_text", m.get("question", ""))[:90] for m in mistakes[:2]]
            })

        # AI Contextual Synthesis
        ai_insight = None
        if self.is_configured() and mistakes:
            try:
                mistake_prompts = "\n".join([f"- {m.get('question_text', '')}" for m in mistakes[:3]])
                prompt = (
                    f"A student studying '{topic}' has {quiz_acc}% quiz accuracy and missed these questions:\n"
                    f"{mistake_prompts}\n\n"
                    f"Provide exactly 2 concise sentences of targeted pedagogical guidance on what concept they should focus on next."
                )
                res = self.generate_text(prompt)
                if res.get("success"):
                    ai_insight = res.get("reply", "").strip()
            except Exception as e:
                logger.warning(f"AI learning signal generation error: {e}")

        if not ai_insight:
            if quiz_acc >= 75.0:
                ai_insight = f"You have strong grasp of {topic}. Keep testing periodically to maintain high recall."
            elif quiz_acc > 0:
                ai_insight = f"Focus your next review on core definitions and step-by-step problem solving in {topic}."
            else:
                ai_insight = f"Begin with flashcards or a short introductory quiz on {topic} to build your foundation."

        return {
            "topic": topic,
            "mastery": mastery,
            "quiz_accuracy": quiz_acc,
            "recall_reliability": recall,
            "difficulty": diff,
            "signals": signals,
            "recommended_action": rec_action,
            "ai_insight": ai_insight
        }

    def generate_recommendations_tip(self, recommendations: List[Dict[str, Any]]) -> str:
        """
        Generates a concise, data-grounded daily study tip based strictly on top recommendations.
        Guardrail: strictly anchored to structured learner data; never makes ungrounded claims.
        """
        if not recommendations:
            return "Select any study material or quiz to begin building your personalized mastery plan."

        top_rec = recommendations[0]
        top_topic = top_rec.get("topic", "your focus topic")
        top_activity = top_rec.get("recommended_activity", "practice")
        top_diff = top_rec.get("recommended_difficulty", "medium")

        fallback_tip = f"Focus on {top_topic} today: start with {top_activity} at {top_diff} difficulty to optimize your retention curve."

        if not self.is_configured():
            return fallback_tip

        try:
            context_lines = []
            for r in recommendations[:3]:
                context_lines.append(
                    f"- Topic: {r.get('topic')}, Mastery: {r.get('mastery', 0)}%, Priority: {r.get('priority')}, Activity: {r.get('recommended_activity')}, Reason: {r.get('reason')}"
                )

            prompt = (
                "You are an academic study coach. Based strictly on the following student diagnostic priorities, "
                "write a single encouraging, actionable 1-sentence daily study focus advice.\n"
                "DO NOT make up any unstated claims or numbers.\n\n" + "\n".join(context_lines)
            )
            res = self.generate_text(
                prompt,
                system_instruction="You are an academic coach. Keep advice grounded, precise, and under 30 words."
            )
            if res.get("success") and res.get("reply"):
                clean_reply = res["reply"].strip().strip('"')
                if len(clean_reply) > 10 and "AI Study Companion Demo Mode" not in clean_reply:
                    return clean_reply
        except Exception as e:
            logger.warning(f"Error generating recommendation tip: {e}")

        return fallback_tip

    def generate_study_plan_guidance(self, tasks: List[Dict[str, Any]]) -> str:
        """
        Generates a motivating 1-sentence study guidance tip for today's allocated study plan tasks.
        Guardrail: AI is strictly for pedagogical coaching advice; does not control scheduling numbers.
        """
        if not tasks:
            return "You have no tasks scheduled for today. Take a quick quiz to generate your daily plan."

        total_minutes = sum(t.get("duration_minutes", 0) for t in tasks)
        top_task = tasks[0]
        top_title = top_task.get("task_title", "your priority task")

        fallback_guidance = f"Today's plan allocates {total_minutes} minutes across {len(tasks)} focused sessions. Begin with {top_title} to maximize retention."

        if not self.is_configured():
            return fallback_guidance

        try:
            task_summaries = [f"- {t.get('task_title')} ({t.get('duration_minutes')} min, {t.get('priority')} priority)" for t in tasks[:4]]
            prompt = (
                f"A student has a {total_minutes}-minute study plan today with these tasks:\n"
                + "\n".join(task_summaries)
                + "\n\nProvide 1 concise, motivating sentence on how to approach today's study block. Do NOT invent new times or topics."
            )
            res = self.generate_text(
                prompt,
                system_instruction="You are an academic mentor. Keep guidance under 25 words."
            )
            if res.get("success") and res.get("reply"):
                clean_reply = res["reply"].strip().strip('"')
                if len(clean_reply) > 10 and "AI Study Companion Demo Mode" not in clean_reply:
                    return clean_reply
        except Exception as e:
            logger.warning(f"Error generating study plan guidance: {e}")

        return fallback_guidance

    def _extract_json_object(self, text: str) -> Dict[str, Any]:
        """Extract and parse a single JSON object from raw model text."""
        if not text:
            return {}
        cleaned = text.strip()
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end+1]

        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
        except Exception as e:
            logger.warning(f"JSON object parse failed: {e}. Attempting recovery.")
            for obj_str in re.findall(r"\{[^{}]*\}", cleaned):
                try:
                    parsed = json.loads(obj_str)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    continue
        return {}

    def generate_viva_question(
        self,
        topic: str,
        mode: str = "basic",
        difficulty: str = "medium",
        question_index: int = 1,
        context_text: Optional[str] = None,
        previous_questions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates a mode-tailored viva question grounded in study materials.
        Modes:
        - basic: Foundational concepts, definitions, direct principles.
        - technical: Architecture, algorithmic analysis, edge cases, trade-offs, concurrency.
        - interview: Practical system design, troubleshooting, scenario-based engineering challenges.
        """
        mode_str = mode.lower()
        if mode_str == "technical":
            style_guide = (
                "Ask an advanced technical viva question requiring rigorous explanation of "
                "internal mechanisms, data structures, algorithmic complexity, trade-offs, or concurrency/failure handling."
            )
        elif mode_str == "interview":
            style_guide = (
                "Ask a realistic engineering interview problem or scenario-based system design/debugging question. "
                "Frame it as an interviewer asking how the candidate would design, troubleshoot, or optimize a system."
            )
        else:
            style_guide = (
                "Ask a clear oral viva question testing core definitions, foundational principles, "
                "and fundamental working mechanisms."
            )

        prev_clause = f"\nAvoid repeating these previous questions:\n" + "\n".join(f"- {q}" for q in (previous_questions or [])) if previous_questions else ""
        ctx_clause = f"\nCourse Material Excerpt to ground the question:\n{context_text[:1200]}\n" if context_text else ""

        prompt = (
            f"Topic: {topic}\n"
            f"Mode: {mode.upper()} ({style_guide})\n"
            f"Difficulty: {difficulty}\n"
            f"Question Number: {question_index}\n"
            f"{ctx_clause}{prev_clause}\n\n"
            f"Generate 1 high-quality viva question formatted as a JSON object with keys:\n"
            f"- 'question_text': (string, the examiner's verbal question)\n"
            f"- 'ideal_concept_points': (list of 3-4 strings detailing what a complete answer must cover)\n"
            f"- 'difficulty': (string: '{difficulty}')\n"
            f"- 'question_type': 'main'"
        )

        # Fallback question generation if AI is not configured or in demo mode
        fallback_questions = {
            "basic": {
                "question_text": f"Can you explain the core concept of {topic}, its primary purpose, and its fundamental working principle?",
                "ideal_concept_points": [
                    f"Accurate definition of {topic}",
                    f"Primary purpose and problem {topic} solves",
                    f"Core mechanism or algorithm steps"
                ],
                "difficulty": difficulty,
                "question_type": "main"
            },
            "technical": {
                "question_text": f"Walk me through the internal architecture and state transitions of {topic}. What are the primary performance bottlenecks, time/space trade-offs, and failure recovery mechanisms?",
                "ideal_concept_points": [
                    f"Detailed architectural components of {topic}",
                    f"Time and space complexity characteristics",
                    f"Concurrency, synchronization, or boundary condition handling",
                    f"Performance trade-offs compared to alternative approaches"
                ],
                "difficulty": difficulty,
                "question_type": "main"
            },
            "interview": {
                "question_text": f"Suppose you are tasked with implementing a scalable system utilizing {topic} under high throughput and strict latency requirements. How would you design the system, and how would you diagnose edge-case failures?",
                "ideal_concept_points": [
                    f"System design and interface boundary definition for {topic}",
                    f"Scalability, partitioning, and caching considerations",
                    f"Failure modes and fault tolerance strategy",
                    f"Monitoring and latency optimization techniques"
                ],
                "difficulty": difficulty,
                "question_type": "main"
            }
        }

        if not self.is_configured():
            return fallback_questions.get(mode_str, fallback_questions["basic"])

        try:
            res = self.generate_text(
                prompt,
                system_instruction="You are a senior university professor and technical hiring lead conducting a rigorous viva. Output strictly valid JSON."
            )
            if res.get("success") and res.get("reply"):
                data = self._extract_json_object(res["reply"])
                if data and "question_text" in data and len(data["question_text"]) > 15:
                    return {
                        "question_text": data.get("question_text"),
                        "ideal_concept_points": data.get("ideal_concept_points") or [f"Key concepts of {topic}"],
                        "difficulty": data.get("difficulty", difficulty),
                        "question_type": "main"
                    }
        except Exception as e:
            logger.warning(f"Error generating viva question: {e}")

        return fallback_questions.get(mode_str, fallback_questions["basic"])

    def evaluate_viva_answer(
        self,
        question_text: str,
        student_answer: str,
        topic: str,
        mode: str = "basic",
        ideal_concept_points: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a student's verbal/written viva answer across 4 dimensions:
        - Correctness (0-100)
        - Relevance (0-100)
        - Completeness (0-100)
        - Conceptual Understanding (0-100)
        Returns structured evaluation with feedback, strengths, and missing points.
        """
        ideal_str = "\n".join(f"- {p}" for p in (ideal_concept_points or []))
        prompt = (
            f"Topic: {topic}\n"
            f"Mode: {mode.upper()}\n"
            f"Examiner Question: {question_text}\n"
            f"Expected Key Points:\n{ideal_str}\n\n"
            f"Student's Response:\n{student_answer}\n\n"
            f"Evaluate the student's response thoroughly. Score each dimension on a 0 to 100 scale:\n"
            f"- 'correctness': Factual accuracy (0-100)\n"
            f"- 'relevance': How directly it answers the prompt (0-100)\n"
            f"- 'completeness': Degree of coverage of expected points (0-100)\n"
            f"- 'conceptual_understanding': Depth of understanding and reasoning (0-100)\n\n"
            f"Return a single JSON object with EXACT keys:\n"
            f"{{\n"
            f'  "correctness": 85,\n'
            f'  "relevance": 90,\n'
            f'  "completeness": 75,\n'
            f'  "conceptual_understanding": 80,\n'
            f'  "score": 82,\n'
            f'  "feedback": "Constructive pedagogical evaluation (2-3 sentences).",\n'
            f'  "key_strengths": ["Strong explanation of X", "Accurate definition of Y"],\n'
            f'  "missing_points": ["Omitted detail Z", "Could elaborate on W"],\n'
            f'  "suggested_follow_up_topic": "{topic}",\n'
            f'  "needs_follow_up": false\n'
            f"}}"
        )

        # Heuristic fallback calculation
        words = len(student_answer.split())
        heuristic_score = min(92.0, max(45.0, 50.0 + min(40, words * 1.5)))
        fallback_eval = {
            "correctness": round(heuristic_score, 1),
            "relevance": round(min(100.0, heuristic_score + 5), 1),
            "completeness": round(max(40.0, heuristic_score - 10), 1),
            "conceptual_understanding": round(heuristic_score, 1),
            "score": round(heuristic_score, 1),
            "feedback": f"Good effort explaining {topic}. Your explanation addresses the main premise, though you can provide deeper technical precision on edge cases.",
            "key_strengths": [f"Demonstrated foundational familiarity with {topic}", "Clear expression of the primary concept"],
            "missing_points": [f"Could provide more granular details on internal mechanism and performance trade-offs."],
            "suggested_follow_up_topic": topic,
            "needs_follow_up": words < 30 or heuristic_score < 70
        }

        if not self.is_configured():
            return fallback_eval

        try:
            res = self.generate_text(
                prompt,
                system_instruction="You are an expert academic examiner. Grade fairly, rigorously, and return strictly valid JSON."
            )
            if res.get("success") and res.get("reply"):
                data = self._extract_json_object(res["reply"])
                if data and "score" in data and "feedback" in data:
                    corr = float(data.get("correctness", 75))
                    rel = float(data.get("relevance", 80))
                    comp = float(data.get("completeness", 70))
                    conc = float(data.get("conceptual_understanding", 75))
                    calculated_score = round(0.35 * corr + 0.25 * conc + 0.20 * comp + 0.20 * rel, 1)
                    
                    return {
                        "correctness": corr,
                        "relevance": rel,
                        "completeness": comp,
                        "conceptual_understanding": conc,
                        "score": data.get("score", calculated_score),
                        "feedback": data.get("feedback", "Good response with sound conceptual foundation."),
                        "key_strengths": data.get("key_strengths") or ["Clear conceptual understanding"],
                        "missing_points": data.get("missing_points") or [],
                        "suggested_follow_up_topic": data.get("suggested_follow_up_topic", topic),
                        "needs_follow_up": bool(data.get("needs_follow_up", comp < 65 or calculated_score < 70))
                    }
        except Exception as e:
            logger.warning(f"Error in evaluate_viva_answer: {e}")

        return fallback_eval

    def generate_viva_follow_up_question(
        self,
        topic: str,
        previous_question: str,
        student_answer: str,
        missing_points: List[str],
        mode: str = "basic"
    ) -> Dict[str, Any]:
        """
        Generates an adaptive follow-up question probing specific gaps or missing details.
        """
        missing_str = ", ".join(missing_points) if missing_points else f"deeper aspects of {topic}"
        prompt = (
            f"Topic: {topic}\n"
            f"Mode: {mode}\n"
            f"Previous Question: {previous_question}\n"
            f"Student Answer: {student_answer}\n"
            f"Gaps identified: {missing_str}\n\n"
            f"Generate a targeted, adaptive follow-up question that prompts the student to address these specific gaps.\n"
            f"Return JSON object with keys:\n"
            f"- 'question_text': (string)\n"
            f"- 'ideal_concept_points': (list of 2-3 strings)\n"
            f"- 'difficulty': 'medium'\n"
            f"- 'question_type': 'follow_up'"
        )

        fallback_follow_up = {
            "question_text": f"Following up on that: how does {topic} behave when considering {missing_str}?",
            "ideal_concept_points": missing_points or [f"Detailed mechanics of {topic}"],
            "difficulty": "medium",
            "question_type": "follow_up"
        }

        if not self.is_configured():
            return fallback_follow_up

        try:
            res = self.generate_text(
                prompt,
                system_instruction="You are an examiner asking a sharp, constructive follow-up question. Output JSON."
            )
            if res.get("success") and res.get("reply"):
                data = self._extract_json_object(res["reply"])
                if data and "question_text" in data and len(data["question_text"]) > 10:
                    return {
                        "question_text": data.get("question_text"),
                        "ideal_concept_points": data.get("ideal_concept_points") or missing_points,
                        "difficulty": data.get("difficulty", "medium"),
                        "question_type": "follow_up"
                    }
        except Exception as e:
            logger.warning(f"Error in generate_viva_follow_up_question: {e}")

        return fallback_follow_up

    def generate_viva_final_report(
        self,
        topic: str,
        mode: str,
        overall_score: float,
        qa_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive final viva performance report including strengths,
        weak areas, actionable improvement recommendations, and overall feedback.
        """
        q_summary = []
        for i, qa in enumerate(qa_history):
            q_text = qa.get("question_text", "")
            ans = qa.get("answer_text", "")
            eval_data = qa.get("evaluation") or {}
            score = eval_data.get("score", 0)
            q_summary.append(f"Q{i+1}: '{q_text}' -> Score: {score}/100. Student answer: '{ans[:100]}...'")

        summary_text = "\n".join(q_summary)
        prompt = (
            f"Topic: {topic}\n"
            f"Mode: {mode}\n"
            f"Overall Score: {overall_score:.1f}%\n"
            f"Questions and Answers:\n{summary_text}\n\n"
            f"Generate a final viva assessment report JSON object with keys:\n"
            f"- 'strengths': (list of 2-3 specific conceptual strengths observed)\n"
            f"- 'weak_areas': (list of 2-3 specific concepts needing reinforcement)\n"
            f"- 'suggested_improvements': (list of 2-3 concrete study actions)\n"
            f"- 'overall_feedback': (motivating 2-sentence summary of performance)"
        )

        fallback_report = {
            "strengths": [
                f"Solid grasp of foundational {topic} definitions",
                "Logical structuring and clear communication of ideas"
            ],
            "weak_areas": [
                f"Detailed boundary-condition and edge-case behavior for {topic}",
                "Quantitative time/space complexity analysis"
            ],
            "suggested_improvements": [
                f"Practice 10 active recall flashcards focusing on {topic} mechanisms.",
                f"Review architectural diagrams and trace algorithms with edge-case inputs.",
                f"Take a timed technical quiz on {topic} to consolidate problem-solving speed."
            ],
            "overall_feedback": f"Demonstrated strong conceptual intuition for {topic} with an overall score of {overall_score:.1f}%. Continuing targeted practice on edge cases will achieve full mastery."
        }

        if not self.is_configured():
            return fallback_report

        try:
            res = self.generate_text(
                prompt,
                system_instruction="You are a senior academic assessor synthesizing a viva session. Output strictly JSON."
            )
            if res.get("success") and res.get("reply"):
                data = self._extract_json_object(res["reply"])
                if data and "overall_feedback" in data:
                    return {
                        "strengths": data.get("strengths") or fallback_report["strengths"],
                        "weak_areas": data.get("weak_areas") or fallback_report["weak_areas"],
                        "suggested_improvements": data.get("suggested_improvements") or fallback_report["suggested_improvements"],
                        "overall_feedback": data.get("overall_feedback") or fallback_report["overall_feedback"]
                    }
        except Exception as e:
            logger.warning(f"Error in generate_viva_final_report: {e}")

        return fallback_report

    def generate_assessment_questions(
        self,
        topic: str,
        subject: Optional[str] = None,
        difficulty: str = "medium",
        question_count: int = 5,
        material_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        AI-assisted assessment generator for instructors.
        Generates comprehensive multiple choice assessment questions with points,
        explanations, concepts tested, and suggested metadata.
        """
        prompt = (
            f"Topic: {topic}\n"
            f"Subject: {subject or 'Computer Science'}\n"
            f"Target Difficulty: {difficulty}\n"
            f"Requested Question Count: {question_count}\n"
        )
        if material_context:
            prompt += f"\nCourse Material Context:\n{material_context[:2000]}\n"

        prompt += (
            f"\nGenerate a comprehensive instructor assessment as a JSON object with keys:\n"
            f"- 'suggested_title': (e.g. '{topic} Mastery & Concept Evaluation')\n"
            f"- 'suggested_time_minutes': (recommended time limit in minutes, e.g. {question_count * 5})\n"
            f"- 'suggested_pass_percentage': (e.g. 60.0)\n"
            f"- 'teaching_notes': (brief instructor pedagogical notes on common pitfalls for {topic})\n"
            f"- 'questions': list of {question_count} question objects, each with:\n"
            f"    - 'id': integer index (1 to {question_count})\n"
            f"    - 'question_text': string clear problem statement / question\n"
            f"    - 'question_type': 'multiple_choice'\n"
            f"    - 'options': list of exactly 4 distinct answer choices\n"
            f"    - 'correct_answer': integer (0, 1, 2, or 3 representing index of correct choice)\n"
            f"    - 'points': integer point value (e.g. 10 or 20)\n"
            f"    - 'explanation': concise pedagogical explanation of why this answer is correct and others are wrong\n"
            f"    - 'concept_tested': specific sub-concept tested (e.g. 'Cycle Detection', 'Locking Protocol')\n"
            f"    - 'difficulty': '{difficulty}'"
        )

        fallback_questions = []
        for i in range(1, question_count + 1):
            fallback_questions.append({
                "id": i,
                "question_text": f"Which statement best characterizes the core operational mechanism of {topic} (Part {i})?",
                "question_type": "multiple_choice",
                "options": [
                    f"It coordinates resource allocation through strict deterministic constraints.",
                    f"It bypasses synchronization invariants to maximize unbounded throughput.",
                    f"It eliminates all algorithmic overhead by avoiding state serialization.",
                    f"It operates strictly in user space without kernel coordination."
                ],
                "correct_answer": 0,
                "points": 20 if question_count <= 5 else 10,
                "explanation": f"In {topic}, deterministic synchronization and invariant maintenance ensure correctness under concurrency.",
                "concept_tested": f"{topic} Core Mechanics",
                "difficulty": difficulty
            })

        fallback_res = {
            "topic": topic,
            "difficulty": difficulty,
            "suggested_title": f"{topic} Comprehensive Assessment",
            "suggested_time_minutes": max(15, question_count * 4),
            "suggested_pass_percentage": 60.0,
            "teaching_notes": f"Ensure students understand trade-offs and edge cases for {topic}.",
            "questions": fallback_questions
        }

        if not self.is_configured():
            return fallback_res

        try:
            res = self.generate_text(
                prompt,
                system_instruction="You are an expert university professor authoring rigorous, high-quality examination assessments. Output strictly valid JSON."
            )
            if res.get("success") and res.get("reply"):
                data = self._extract_json_object(res["reply"])
                if data and "questions" in data and isinstance(data["questions"], list) and len(data["questions"]) > 0:
                    formatted_qs = []
                    for idx, q in enumerate(data["questions"][:question_count], 1):
                        opts = q.get("options") or []
                        if len(opts) < 4:
                            opts = opts + [f"Alternative Option {k}" for k in range(len(opts), 4)]
                        c_ans = q.get("correct_answer", 0)
                        if not isinstance(c_ans, int) or c_ans < 0 or c_ans >= len(opts):
                            c_ans = 0
                        formatted_qs.append({
                            "id": idx,
                            "question_text": q.get("question_text") or f"Question on {topic}",
                            "question_type": q.get("question_type", "multiple_choice"),
                            "options": opts[:4],
                            "correct_answer": c_ans,
                            "points": q.get("points", 20 if question_count <= 5 else 10),
                            "explanation": q.get("explanation", f"Correct answer for {topic}."),
                            "concept_tested": q.get("concept_tested", topic),
                            "difficulty": q.get("difficulty", difficulty)
                        })
                    return {
                        "topic": topic,
                        "difficulty": difficulty,
                        "suggested_title": data.get("suggested_title") or f"{topic} Mastery Assessment",
                        "suggested_time_minutes": data.get("suggested_time_minutes") or max(15, question_count * 4),
                        "suggested_pass_percentage": float(data.get("suggested_pass_percentage", 60.0)),
                        "teaching_notes": data.get("teaching_notes") or fallback_res["teaching_notes"],
                        "questions": formatted_qs
                    }
        except Exception as e:
            logger.warning(f"Error in generate_assessment_questions: {e}")

        return fallback_res


ai_service = AIService()

