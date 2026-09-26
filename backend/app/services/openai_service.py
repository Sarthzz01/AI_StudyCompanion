import os
import time
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("uvicorn.error")

DEFAULT_TUTOR_INSTRUCTIONS = (
    "You are a helpful AI tutor. Answer the student's questions accurately and clearly. "
    "Explain concepts in a way appropriate for the student's level. Use examples when useful. "
    "For educational questions, prioritize helping the student understand the concept rather than "
    "simply giving an unexplained answer. If the question is ambiguous, ask for clarification. "
    "Do not invent facts when you are uncertain."
)

class OpenAIService:
    """
    OpenAI LLM Integration service using the official OpenAI Python SDK Responses API.
    Designed for educational AI tutoring across subjects:
    Mathematics, Science, History, Programming, General Knowledge, English, etc.
    """
    def __init__(self):
        self._client = None
        self._custom_instruction: Optional[str] = None

    @property
    def api_key(self) -> str:
        return settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "").strip()

    @property
    def model_name(self) -> str:
        return settings.OPENAI_MODEL or os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    @property
    def client(self):
        if self._client is None and self.is_configured():
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self._client = None
        return self._client

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_instructions(self) -> str:
        return self._custom_instruction or DEFAULT_TUTOR_INSTRUCTIONS

    def set_instructions(self, instruction: str):
        """Allows modifying tutor behavior system/developer prompt at runtime."""
        self._custom_instruction = instruction

    def generate_tutor_response(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = None,
        context_excerpts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates an educational tutor response using OpenAI's Responses API.
        Includes previous conversation history for contextual follow-up questions.
        Handles all general subjects (Science, Math, History, Coding, Literature, etc.).
        """
        start_time = time.time()
        instructions = system_instruction or self.get_instructions()

        # If study material context excerpts are available, append them to instructions
        if context_excerpts:
            joined_context = "\n---\n".join(context_excerpts)
            instructions = (
                f"{instructions}\n\n"
                f"Reference Material:\n{joined_context}\n\n"
                f"When relevant to the question, incorporate insights from the reference material."
            )

        # Build conversation input for OpenAI Responses API
        # The Responses API accepts a list of message objects for multi-turn history
        input_items = []
        if history:
            for item in history:
                role = item.get("role")
                content = item.get("content")
                if role in ["user", "assistant"] and content:
                    input_items.append({"role": role, "content": str(content)})

        # Append current user question
        input_items.append({"role": "user", "content": message.strip()})

        # 1. Attempt OpenAI Responses API if configured
        if self.is_configured():
            try:
                logger.info(f"Dispatching query to OpenAI Responses API (model: {self.model_name})...")
                client = self.client
                if client:
                    try:
                        response = client.responses.create(
                            model=self.model_name,
                            instructions=instructions,
                            input=input_items,
                        )
                        output_text = getattr(response, "output_text", None)
                        if not output_text and hasattr(response, "output"):
                            # Fallback extraction from output items if output_text is empty
                            for out_item in response.output:
                                if hasattr(out_item, "content"):
                                    output_text = str(out_item.content)
                                    break
                                elif isinstance(out_item, dict) and "content" in out_item:
                                    output_text = str(out_item["content"])
                                    break

                        if output_text:
                            latency_ms = int((time.time() - start_time) * 1000)
                            return {
                                "answer": output_text.strip(),
                                "model": self.model_name,
                                "latency_ms": latency_ms,
                                "source": "openai-responses"
                            }
                    except Exception as resp_err:
                        logger.warning(f"Responses API returned error: {resp_err}. Trying chat completions fallback...")
                        # Fallback to chat completions if responses endpoint has tier/model constraints
                        chat_messages = [{"role": "developer", "content": instructions}]
                        chat_messages.extend(input_items)
                        completion = client.chat.completions.create(
                            model=self.model_name,
                            messages=chat_messages,
                        )
                        answer = completion.choices[0].message.content or ""
                        latency_ms = int((time.time() - start_time) * 1000)
                        return {
                            "answer": answer.strip(),
                            "model": self.model_name,
                            "latency_ms": latency_ms,
                            "source": "openai-chat"
                        }
            except Exception as e:
                logger.error(f"OpenAI API execution error: {e}")
                # Fall through to fallback generation rather than crashing or exposing secrets

        # 2. Resilient fallback: Gemini AI or domain-rich educational knowledge
        logger.info("Using secondary educational AI engine for tutor response...")
        try:
            from app.services.ai_service import ai_service
            if ai_service.is_configured():
                # Format full prompt with conversation history for Gemini
                conv_history_str = ""
                if history:
                    recent = history[-6:]  # Last 6 exchanges
                    conv_history_str = "\n".join(f"{h.get('role', 'user').capitalize()}: {h.get('content', '')}" for h in recent) + "\n"
                
                full_prompt = (
                    f"{conv_history_str}"
                    f"Student: {message}\n"
                    f"Tutor:"
                )
                res = ai_service.generate_text(prompt=full_prompt, system_instruction=instructions)
                if res.get("success") and res.get("reply"):
                    latency_ms = int((time.time() - start_time) * 1000)
                    return {
                        "answer": res["reply"].strip(),
                        "model": res.get("model", "gemini-ai"),
                        "latency_ms": latency_ms,
                        "source": "gemini-fallback"
                    }
        except Exception as gemini_err:
            logger.warning(f"Secondary AI engine error: {gemini_err}")

        # 3. Clean, educational knowledge fallback for common concepts
        fallback_answer = self._generate_conceptual_explanation(message)
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "answer": fallback_answer,
            "model": "tutor-foundation",
            "latency_ms": latency_ms,
            "source": "local-tutor"
        }

    def _generate_conceptual_explanation(self, query: str) -> str:
        """
        Provides structured conceptual explanations when external API connectivity is offline.
        Handles key academic topics (Photosynthesis, Algorithms, Calculus, Newton's Laws, etc.).
        """
        q = query.lower()
        if "photosynthesis" in q:
            return (
                "**Photosynthesis** is the biological process by which green plants, algae, and certain bacteria "
                "convert light energy (usually from the Sun) into chemical energy stored in glucose molecules.\n\n"
                "### The Overall Chemical Equation:\n"
                "$$6\\text{CO}_2 + 6\\text{H}_2\\text{O} + \\text{light} \\rightarrow \\text{C}_6\\text{H}_{12}\\text{O}_6 + 6\\text{O}_2$$\n\n"
                "### Key Stages:\n"
                "1. **Light-Dependent Reactions (in Thylakoid membranes):** Chlorophyll absorbs photons, splitting water ($H_2O$) to release oxygen ($O_2$) and generating energy carriers (ATP and NADPH).\n"
                "2. **Light-Independent Reactions / Calvin Cycle (in the Stroma):** The plant uses ATP and NADPH to fix atmospheric carbon dioxide ($CO_2$) into high-energy sugars (glucose).\n\n"
                "**Why it matters:** Photosynthesis is the foundation of Earth's oxygen supply and the primary energy source for nearly all food chains!"
            )
        elif "binary search tree" in q or "bst" in q:
            return (
                "A **Binary Search Tree (BST)** is a hierarchical node-based data structure with the following properties:\n\n"
                "- The left subtree of a node contains only keys **less** than the node's key.\n"
                "- The right subtree of a node contains only keys **greater** than the node's key.\n"
                "- Both left and right subtrees must also be binary search trees.\n\n"
                "### Time Complexity:\n"
                "- **Search / Insert / Delete (Average / Balanced):** $O(\\log n)$\n"
                "- **Worst Case (Skewed):** $O(n)$\n\n"
                "Balanced variants like **AVL Trees** and **Red-Black Trees** maintain $O(\\log n)$ worst-case guarantees."
            )
        elif "recursion" in q:
            return (
                "**Recursion** is a programming technique where a function solves a problem by calling itself with a smaller subproblem.\n\n"
                "### Every recursive function requires two parts:\n"
                "1. **Base Case:** A terminating condition that stops the recursion without further calls.\n"
                "2. **Recursive Step:** The logic that divides the problem and invokes the function on the smaller input.\n\n"
                "### Example: Factorial in Python\n"
                "```python\n"
                "def factorial(n):\n"
                "    if n <= 1:       # Base case\n"
                "        return 1\n"
                "    return n * factorial(n - 1)  # Recursive call\n"
                "```"
            )
        else:
            return (
                f"Here is an overview of **{query.strip()}**:\n\n"
                "To understand this concept effectively:\n"
                "1. **Core Definition:** Break down the fundamental principles and terminology.\n"
                "2. **Application:** Relate it to practical examples and real-world use cases.\n"
                "3. **Key Relationships:** Notice how it connects with related foundational topics.\n\n"
                "Feel free to ask a specific follow-up question or request an example!"
            )

    def generate_conversation_title(
        self,
        first_message: str,
        first_answer: Optional[str] = None
    ) -> str:
        """
        Generates a concise, smart title (3 to 6 words) summarizing what the whole conversation is about.
        Uses OpenAI if available, with intelligent semantic fallback.
        """
        if self.is_configured():
            try:
                client = self.client
                if client:
                    summary_context = f"Student query: {first_message.strip()}"
                    if first_answer:
                        summary_context += f"\nTutor response snippet: {first_answer[:250].strip()}"

                    prompt = (
                        "Generate a short, concise, high-level title (3 to 5 words maximum, no quotes, no trailing punctuation) "
                        "that accurately captures what this study discussion is about based on the student's question and explanation:\n\n"
                        f"{summary_context}\n\n"
                        "Title:"
                    )

                    completion = client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": "You are a concise academic assistant that creates short 3-5 word titles for study discussions."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=20,
                        temperature=0.3,
                    )
                    title = completion.choices[0].message.content or ""
                    cleaned = title.strip().strip('"\'').strip()
                    if cleaned:
                        return cleaned[:50]
            except Exception as e:
                logger.warning(f"Could not generate AI title with OpenAI: {e}")

        # Intelligent fallback: extract topic from query
        clean = first_message.strip()
        for prefix in ["what is ", "what are ", "explain ", "can you explain ", "tell me about ", "how does ", "how do i ", "how to ", "write a "]:
            if clean.lower().startswith(prefix):
                clean = clean[len(prefix):].strip()
                break
        clean = clean.split("?")[0].split(".")[0].strip()
        words = clean.split()
        if len(words) > 5:
            return " ".join(words[:5]).title()
        return clean.title() if clean else "Study Discussion"

openai_service = OpenAIService()
