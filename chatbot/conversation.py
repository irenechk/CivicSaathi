"""
Stateful Multi-Turn Conversation Manager for Civicsaathi.
Handles natural citizen dialogues, profile updates, scheme questions, and reset workflows.
"""

from typing import Dict, Any, List, Optional
from database.models import CitizenProfile
from chatbot.profile_extractor import ProfileExtractor
from chatbot.question_manager import QuestionManager
from rag.retriever import HybridRetriever
from rag.answer_generator import AnswerGenerator


class ConversationManager:
    def __init__(self, retriever: HybridRetriever, answer_generator: AnswerGenerator):
        self.retriever = retriever
        self.answer_generator = answer_generator

    def process_message(
        self,
        user_message: str,
        profile: CitizenProfile,
        chat_history: List[Dict[str, str]],
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Processes citizen input:
        1. Checks for reset or deletion command
        2. Extracts profile attributes from the message
        3. Answers scheme questions using local RAG
        4. Prompts for next profile question if incomplete
        """
        msg_clean = user_message.strip().lower()

        # 1. Reset / Deletion intent
        if msg_clean in ("reset", "delete profile", "restart", "start over", "माहिती हटवा", "मिटाएं"):
            new_profile = CitizenProfile(language=language)
            confirm_msg = {
                "en": "Your profile information has been cleared. Let's start fresh! How can I help you today?",
                "hi": "आपकी प्रोफाइल जानकारी हटा दी गई है। आइए नए सिरे से शुरुआत करें! आज मैं आपकी क्या मदद कर सकता हूँ?",
                "mr": "आपली प्रोफाइल माहिती हटवण्यात आली आहे. नव्याने सुरुवात करूया! आज मी आपल्याला कशी मदत करू शकेन?",
            }.get(language, "Profile reset.")
            return {
                "reply": confirm_msg,
                "profile": new_profile,
                "citations": [],
            }

        # 2. Extract profile attributes
        updated_profile = ProfileExtractor.extract_from_text(user_message, profile)

        # 3. Retrieve relevant scheme passages
        retrieved = self.retriever.retrieve(
            query=user_message,
            top_k=3,
            state_filter=updated_profile.state,
        )

        rag_output = self.answer_generator.generate_answer(
            query=user_message,
            retrieved_passages=retrieved,
            language=language,
        )

        # 4. Check if profile needs next question
        next_q = QuestionManager.get_next_question(updated_profile, language=language)
        reply = rag_output["answer"]

        if next_q and len(retrieved) > 0:
            prompt_extra = {
                "en": f"\n\n👉 *To check your exact eligibility:* {next_q['question']}",
                "hi": f"\n\n👉 *सटीक पात्रता जानने के लिए:* {next_q['question']}",
                "mr": f"\n\n👉 *अचूक पात्रता तपासण्यासाठी:* {next_q['question']}",
            }.get(language, f"\n\n{next_q['question']}")
            reply += prompt_extra
        elif next_q and len(retrieved) == 0:
            reply = next_q["question"]

        return {
            "reply": reply,
            "profile": updated_profile,
            "citations": rag_output.get("citations", []),
            "engine": rag_output.get("engine", "knowledge_engine"),
        }
