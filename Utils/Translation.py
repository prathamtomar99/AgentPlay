# React Agnet responsilbe for translation audio from a Source Language to Target Language
# Test/TranslationAgent.ipynb for more infomration 
# Used PolyRouter : https://github.com/prathamtomar99/PolyRouter


from Utils.Singleton import Singleton
from Utils.Exception import UnsupportedLanguage
from config import GEMINI_KEYS, GEMINI_MODEL, CEREBRAS_KEYS, CEREBRAS_MODEL, GROQ_KEYS, GROQ_MODEL, LANGUAGE_MAP
from langgraph.graph import StateGraph, START, END
import json
from typing import TypedDict
from polyrouter import LLMOrchestrator
import logging
logger = logging.getLogger(__name__)


### React Agent

# @Singleton
# class TranslatorAgent():
#     def __init__(self):
#         self.LLM = LLMOrchestrator(
#             groq={
#                 "groq_models" : GROQ_MODEL,
#                 "groq_keys" : GROQ_KEYS,
#             },
#             # gemini={ # has the least limits : better avoid using
#             #     "gemini_models" : GEMINI_MODEL,
#             #     "gemini_keys" : GEMINI_KEYS,
#             # },
#             cerebras={
#                 "cerebras_models": CEREBRAS_MODEL,
#                 "cerebras_keys" : CEREBRAS_KEYS
#             },
#             debug=1,        # major logs
#             verbose=1,      # in-depth trace
#             prompt="Be Specific",
#             temperature=0.2,
#             max_output_tokens=400,
#         )
#         class AgentState(TypedDict):
#             PREVIOUS_SEGMENT : str
#             CURRENT_SEGMENT : str
#             FUTURE_SEGMENT : str
#             TARGET_LANGUAGE : str
#             ITERATIONS : int
#             FEEDBACK : dict
#             TRANSLATED_TEXT : str

#         def translate_llm(state):
#             fb = state.get("FEEDBACK", {})

#             logger.debug("translate_llm: starting (TARGET=%s, ITER=%s)", state.get('TARGET_LANGUAGE'), state.get('ITERATIONS'))

#             feedback_text = ""
#             if fb and fb.get('status') == 'INVALID':
#                 feedback_text = f"""
#                     [PREVIOUS ATTEMPT FEEDBACK]
#                     The validator rejected your last translation for this reason:
#                     "{fb.get('issues')}"

#                     ACTION REQUIRED: Fix this issue in your next output. You must apply this feedback SILENTLY. Do not acknowledge the mistake, do not add notes, and do not include any text other than the final translation.
#                     """

#             prompt = f"""
#                 You are a highly precise contextual translation agent.

#                 Task:
#                 Translate ONLY the text within the [TARGET TO TRANSLATE] block into {state.get('TARGET_LANGUAGE', 'English')}.

#                 Rules:
#                 1. STRICT SCOPE: Do not translate the context blocks.
#                 2. CONTEXT USAGE: Use context blocks strictly to resolve ambiguities (e.g., tone, tense, pronoun resolution).
#                 3. NO FILLER: Output exactly the translated string and nothing else. No conversational text, no brackets, no introductory phrases.

#                 {feedback_text}
#                 --- INPUT DATA ---

#                 [CONTEXT - DO NOT TRANSLATE]
#                 PREVIOUS: {state.get('PREVIOUS_SEGMENT','')}

#                 [CONTEXT - DO NOT TRANSLATE]
#                 FUTURE: {state.get('FUTURE_SEGMENT','')}

#                 [TARGET TO TRANSLATE]
#                 {state.get('CURRENT_SEGMENT','')}
#                 """

#             try:
#                 translated_text = self.LLM.call(prompt)
#                 translated_text = translated_text.strip() if isinstance(translated_text, str) else translated_text
#                 logger.debug("translate_llm: translated_text (len=%d)", len(translated_text) if isinstance(translated_text, str) else 0)
#             except Exception as e:
#                 logger.exception("translate_llm: LLM.call failed")
#                 translated_text = ""

#             state["TRANSLATED_TEXT"] = translated_text
#             return state
        
#         def validator_llm(state):
#             logger.debug("validator_llm: starting (ITER=%s)", state.get('ITERATIONS'))

#             prompt = f"""   
#                 You are a lenient and practical translation validation agent.

#                 Task:
#                 Evaluate whether TRANSLATED_TEXT is an acceptable, understandable translation of the CURRENT_SEGMENT into {state["TARGET_LANGUAGE"]}.

#                 Rules:
#                 1. CONVERSATIONAL LENIENCY (CRITICAL): The source text is from a raw YouTube transcript. It contains slang, fragmented sentences, and informal speech. DO NOT reject the translation for minor grammatical flaws (e.g., missing articles like "a" or "the", or slightly awkward syntax) as long as the core meaning is understandable.
#                 2. FOCUS STRICTLY ON THE TARGET: Only evaluate the translation of the CURRENT_SEGMENT.
#                 3. USE CONTEXT PROPERLY: Use PREVIOUS_SEGMENT and FUTURE_SEGMENT ONLY to resolve ambiguities (e.g., pronouns, tense). 
#                 4. DO NOT PENALIZE OMISSIONS: Do NOT penalize the TRANSLATED_TEXT for omitting words or concepts that belong to the surrounding context segments.
#                 5. Return ONLY valid JSON.

#                 If translation is acceptable (even if informal or imperfect):
#                 {{
#                     "status": "VALID",
#                     "issues": ""
#                 }}

#                 If translation completely fails to convey the meaning or is utterly broken:
#                 {{
#                     "status": "INVALID",
#                     "issues": "Short, specific reason focusing ONLY on the critical failure in the CURRENT_SEGMENT."
#                 }}

#                 [CONTEXT - DO NOT EXPECT THIS TO BE TRANSLATED]
#                 PREVIOUS_SEGMENT:
#                 {state["PREVIOUS_SEGMENT"]}

#                 [TARGET - THIS IS WHAT MUST BE TRANSLATED]
#                 CURRENT_SEGMENT:
#                 {state["CURRENT_SEGMENT"]}

#                 TARGET_LANGUAGE:
#                 {state["TARGET_LANGUAGE"]}

#                 TRANSLATED_TEXT:
#                 {state["TRANSLATED_TEXT"]}

#                 [CONTEXT - DO NOT EXPECT THIS TO BE TRANSLATED]
#                 FUTURE_SEGMENT:
#                 {state["FUTURE_SEGMENT"]}
#                 """
            
#             # Ensure the response is properly parsed into a dictionary
#             try:
#                 raw_response = self.LLM.call(prompt, json_mode=1)
#                 logger.debug("validator_llm: raw_response type=%s", type(raw_response))
#                 validator_res = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
#             except json.JSONDecodeError:
#                 logger.warning("validator_llm: Failed to parse JSON from LLM response, forcing VALID")
#                 validator_res = {"status": "VALID", "issues": "Failed to parse JSON, forcing valid to continue."}
#             except Exception as e:
#                 logger.exception("validator_llm: LLM.call or processing failed")
#                 validator_res = {"status": "VALID", "issues": str(e)}

#             state["ITERATIONS"] += 1
#             state["FEEDBACK"] = validator_res
#             logger.debug("validator_llm: validator_res=%s", validator_res)
#             return state
        

#         def should_continue(state):
#         #     print(state)
#             status = state.get("FEEDBACK", {}).get("status")
#             logger.debug("should_continue: status=%s iterations=%s", status, state.get("ITERATIONS"))
#             if status == "VALID":
#                 return "end"
#             else:
#                 if state.get("ITERATIONS", 0) > 3:
#                     return "end"
#                 return "continue"
            
#         workflow = StateGraph(AgentState)
#         workflow.add_node("Translator",translate_llm)
#         workflow.add_node("Validator",validator_llm)
#         workflow.add_conditional_edges(
#             "Validator", 
#             should_continue,
#             {
#                 "end": END,
#                 "continue": "Translator"
#             }
#         )
#         workflow.add_edge(START, "Translator")
#         workflow.add_edge("Translator", "Validator")
#         self.app = workflow.compile()

#     def call(self,PREVIOUS_SEGMENT,CURRENT_SEGMENT,FUTURE_SEGMENT,TARGET_LANGUAGE_ABBREVIATION):
#         TARGET_LANGUAGE = LANGUAGE_MAP.get(TARGET_LANGUAGE_ABBREVIATION)
#         if(TARGET_LANGUAGE is None):
#             raise UnsupportedLanguage(f"[Translation.py:] {TARGET_LANGUAGE_ABBREVIATION} is not supported.")
#         initial_state = {
#             "PREVIOUS_SEGMENT": PREVIOUS_SEGMENT,
#             "CURRENT_SEGMENT": CURRENT_SEGMENT,
#             "FUTURE_SEGMENT": FUTURE_SEGMENT,
#             "TRANSLATED_TEXT": "",
#             "TARGET_LANGUAGE": TARGET_LANGUAGE,
#             "ITERATIONS": 0,
#             "FEEDBACK": None
#         }
#         logger.debug("call: invoking workflow for target=%s", TARGET_LANGUAGE_ABBREVIATION)
#         try:
#             final_state = self.app.invoke(initial_state)
#             logger.debug("call: final_state keys=%s", list(final_state.keys()) if isinstance(final_state, dict) else type(final_state))
#         except Exception as e:
#             logger.exception("call: workflow invocation failed")
#             return ""

#         return final_state.get("TRANSLATED_TEXT", "")
    


### COT
## If usng COR - use good models like OSS120b etc in config.py

@Singleton
class TranslatorAgent():
    def __init__(self):
        # We only need one LLM instance now.
        self.LLM = LLMOrchestrator(
            groq={
                "groq_models": GROQ_MODEL,
                "groq_keys": GROQ_KEYS,
            },
            cerebras={
                "cerebras_models": CEREBRAS_MODEL,
                "cerebras_keys": CEREBRAS_KEYS
            },
            debug=1,
            verbose=1,
            prompt="You are an expert bilingual translator.",
            temperature=0.2, 
            max_output_tokens=500, # Increased slightly to give room for the "thoughts"
        )

    def call(self, PREVIOUS_SEGMENT, CURRENT_SEGMENT, FUTURE_SEGMENT, TARGET_LANGUAGE_ABBREVIATION):
        TARGET_LANGUAGE = LANGUAGE_MAP.get(TARGET_LANGUAGE_ABBREVIATION)
        
        if TARGET_LANGUAGE is None:
            raise UnsupportedLanguage(f"[Translation.py:] {TARGET_LANGUAGE_ABBREVIATION} is not supported.")

        # Handle None values safely for the prompt
        prev_text = PREVIOUS_SEGMENT if PREVIOUS_SEGMENT else "None"
        future_text = FUTURE_SEGMENT if FUTURE_SEGMENT else "None"

        # The Chain of Thought Prompt
        prompt = f"""
        You are an expert bilingual translator specialized in converting casual, colloquial internet transcripts (often Hinglish or slang) into natural {TARGET_LANGUAGE}.

        Task: Translate the [TARGET TEXT] into {TARGET_LANGUAGE}. 

        To ensure the highest accuracy, follow these steps sequentially within your thought process:
        1. Identify the literal meaning of slang, phonetic internet words, or broken sentences.
        2. Draft an initial translation based on the literal meaning.
        3. Review your draft. Fix awkward wording, but DO NOT drop any information. 
        
        CRITICAL RULES:
        - PRESERVE FRAGMENTS: YouTube transcripts are often broken sentences. If the [TARGET TEXT] is a fragment, your translation MUST also be a fragment. Do not attempt to force it into a complete, standalone sentence by deleting words.
        - NO OMISSIONS: You must translate every part of the [TARGET TEXT]. 

        Input Data:
        [CONTEXT] Previous Segment: {prev_text}
        [CONTEXT] Future Segment: {future_text}
        [TARGET TEXT]: {CURRENT_SEGMENT}

        Output format:
        Return ONLY a valid JSON object matching this exact structure, with no conversational filler outside the JSON:
        {{
            "analysis": "Write a 1-2 sentence thought process here about how you translated the fragment without losing information.",
            "final_translation": "The accurate {TARGET_LANGUAGE} translation here."
        }}
        """

        try:
            # Force JSON mode so we can easily parse the thoughts vs the final output
            raw_response = self.LLM.call(prompt, json_mode=1)
            
            # Parse the response safely
            parsed_res = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
            
            final_text = parsed_res.get("final_translation", "").strip()
            analysis_text = parsed_res.get("analysis", "")
            
            # Optional: Log the LLM's thought process so you can see it working in your terminal!
            logger.debug(f"LLM Thoughts: {analysis_text}")
            
            # Fallback if the LLM returned empty translation somehow
            if not final_text:
                return CURRENT_SEGMENT
                
            return final_text

        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from LLM response. Returning original text. Raw output: {raw_response}")
            return CURRENT_SEGMENT
            
        except Exception as e:
            logger.error(f"Unexpected error in translation CoT: {e}")
            return CURRENT_SEGMENT


if __name__=="__main__":


    # React testing

    # TAgent = TranslatorAgent()
    # import logging
    # logger = logging.getLogger(__name__)
    # logger.info(TAgent.call("The research team completed the prototype testing phase last week.",
    #             "The system now processes multilingual audio streams in real time with low latency.",
    #             "It will be deployed across edge devices globally.",
    #             "Hindi",
    #             ))


    # COT Testing

    TAgent = TranslatorAgent()
    logging.basicConfig(level=logging.DEBUG)
    
    # Test with the problematic Hinglish string
    test_result = TAgent.call(
        "फाइनली बांदा ट्वीट करता है एंड डी बर्ड",
        "इस नो फ्री एंड जैसे ही वो ट्वीट करता है",
        "चूहे के पूरे न्यूज़ हेडलाइंस में न्यूज़",
        "en" # Assuming 'en' maps to 'English' in your LANGUAGE_MAP
    )
    print(f"\nFinal Result: {test_result}")