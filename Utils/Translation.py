from Utils.Singleton import Singleton
from Utils.Exception import UnsupportedLanguage
from config import GEMINI_KEYS, GEMINI_MODEL, CEREBRAS_KEYS, CEREBRAS_MODEL, GROQ_KEYS, GROQ_MODEL, LANGUAGE_MAP
from langgraph.graph import StateGraph, START, END
import json
from typing import TypedDict
from polyrouter import LLMOrchestrator

LLM = LLMOrchestrator(
    groq={
        "groq_models" : GROQ_MODEL,
        "groq_keys" : GROQ_KEYS,
    },
    cerebras={
        "cerebras_models": CEREBRAS_MODEL,
        "cerebras_keys" : CEREBRAS_KEYS
    },
    debug=1,        # major logs
    verbose=1,      # in-depth trace
    prompt="Be Specific",
    temperature=0.2,
    max_output_tokens=400,
)

@Singleton
class TranslatorAgent():
    def __init__(self):
        class AgentState(TypedDict):
            PREVIOUS_SEGMENT : str
            CURRENT_SEGMENT : str
            FUTURE_SEGMENT : str
            TARGET_LANGUAGE : str
            ITERATIONS : int
            FEEDBACK : dict
            TRANSLATED_TEXT : str

        def translate_llm(state):
            fb = state.get("FEEDBACK", {})

            feedback_text = ""
            if fb and fb.get('status') == 'INVALID':
                feedback_text = f"""
                    [PREVIOUS ATTEMPT FEEDBACK]
                    The validator rejected your last translation for this reason:
                    "{fb.get('issues')}"

                    ACTION REQUIRED: Fix this issue in your next output. You must apply this feedback SILENTLY. Do not acknowledge the mistake, do not add notes, and do not include any text other than the final translation.
                    """

            prompt = f"""
                You are a highly precise contextual translation agent.

                Task:
                Translate ONLY the text within the [TARGET TO TRANSLATE] block into {state.get('TARGET_LANGUAGE', 'English')}.

                Rules:
                1. STRICT SCOPE: Do not translate the context blocks.
                2. CONTEXT USAGE: Use context blocks strictly to resolve ambiguities (e.g., tone, tense, pronoun resolution).
                3. NO FILLER: Output exactly the translated string and nothing else. No conversational text, no brackets, no introductory phrases.

                {feedback_text}
                --- INPUT DATA ---

                [CONTEXT - DO NOT TRANSLATE]
                PREVIOUS: {state.get('PREVIOUS_SEGMENT','')}

                [CONTEXT - DO NOT TRANSLATE]
                FUTURE: {state.get('FUTURE_SEGMENT','')}

                [TARGET TO TRANSLATE]
                {state.get('CURRENT_SEGMENT','')}
                """

            translated_text = LLM.call(prompt).strip()
            state["TRANSLATED_TEXT"] = translated_text
            return state
        
        def validator_llm(state):
            prompt = f"""   
                You are a strict translation validation agent.

                Task:
                Validate whether TRANSLATED_TEXT is an accurate, grammatically correct, and natural translation of ONLY the CURRENT_SEGMENT into {state["TARGET_LANGUAGE"]}.

                Rules:
                1. FOCUS STRICTLY ON THE TARGET: You must only evaluate the translation of the CURRENT_SEGMENT.
                2. HOW TO USE CONTEXT: You are provided with PREVIOUS_SEGMENT and FUTURE_SEGMENT. Use these ONLY to resolve ambiguities in the CURRENT_SEGMENT (e.g., pronoun resolution, maintaining correct tense, or understanding the overall domain). 
                3. EXPLICIT NEGATIVE CONSTRAINT: Do NOT penalize the TRANSLATED_TEXT for omitting words, phrases, or concepts that belong to the PREVIOUS_SEGMENT or FUTURE_SEGMENT.
                4. Return ONLY valid JSON. Do not return explanations outside JSON.

                If translation is correct:
                {{
                    "status": "VALID",
                    "issues": ""
                }}

                If translation is incorrect:
                {{
                    "status": "INVALID",
                    "issues": "Short reason here, focusing ONLY on errors within the CURRENT_SEGMENT."
                }}

                --- INPUT DATA ---

                [CONTEXT - DO NOT EXPECT THIS TO BE TRANSLATED]
                PREVIOUS_SEGMENT:
                {state["PREVIOUS_SEGMENT"]}

                [TARGET - THIS IS WHAT MUST BE TRANSLATED]
                CURRENT_SEGMENT:
                {state["CURRENT_SEGMENT"]}

                TARGET_LANGUAGE:
                {state["TARGET_LANGUAGE"]}

                TRANSLATED_TEXT:
                {state["TRANSLATED_TEXT"]}

                [CONTEXT - DO NOT EXPECT THIS TO BE TRANSLATED]
                FUTURE_SEGMENT:
                {state["FUTURE_SEGMENT"]}
                """
            validator_res = LLM.call(prompt, json_mode=1)
            state["ITERATIONS"] += 1
            state["FEEDBACK"] = validator_res
            return state
        
        def should_continue(state):
        #     print(state)
            if(state["FEEDBACK"]["status"] == "VALID"):
                return "end"
            else:
                if(state["ITERATIONS"]>3):
                    return "end"
                return "continue"
            
        workflow = StateGraph(AgentState)
        workflow.add_node("Translator",translate_llm)
        workflow.add_node("Validator",validator_llm)
        workflow.add_conditional_edges(
            "Validator", 
            should_continue,
            {
                "end": END,
                "continue": "Translator"
            }
        )
        workflow.add_edge(START, "Translator")
        workflow.add_edge("Translator", "Validator")
        self.app = workflow.compile()

    def call(self,PREVIOUS_SEGMENT,CURRENT_SEGMENT,FUTURE_SEGMENT,TARGET_LANGUAGE_ABBREVIATION):
        TARGET_LANGUAGE = LANGUAGE_MAP.get(TARGET_LANGUAGE_ABBREVIATION)
        if(TARGET_LANGUAGE is None):
            raise UnsupportedLanguage(f"[Translation.py:] {TARGET_LANGUAGE_ABBREVIATION} is not supported.")
        initial_state = {
            "PREVIOUS_SEGMENT": PREVIOUS_SEGMENT,
            "CURRENT_SEGMENT": CURRENT_SEGMENT,
            "FUTURE_SEGMENT": FUTURE_SEGMENT,
            "TRANSLATED_TEXT": "",
            "TARGET_LANGUAGE": TARGET_LANGUAGE,
            "ITERATIONS": 0,
            "FEEDBACK": None
        }
        final_state = self.app.invoke(initial_state)
        # print(final_state)
        return final_state.get("TRANSLATED_TEXT", "")
    
if __name__=="__main__":
    TAgent = TranslatorAgent()
    print(TAgent.call("The research team completed the prototype testing phase last week.",
                "The system now processes multilingual audio streams in real time with low latency.",
                "It will be deployed across edge devices globally.",
                "Hindi",
                ))