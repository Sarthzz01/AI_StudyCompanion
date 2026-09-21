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
                "reply": f"[AI Study Companion Demo Mode]: Processed prompt '{prompt[:60]}...'. To activate live Gemini intelligence, set GEMINI_API_KEY in backend/.env.",
                "model": "demo-fallback",
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

ai_service = AIService()

