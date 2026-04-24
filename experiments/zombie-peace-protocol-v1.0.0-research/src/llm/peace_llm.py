"""
LLM for Peace Protocol Module

This module utilizes the Qwen3.6 LLM to extract implied peace messages from lyrics
and apply ethical filtering to ensure message integrity.
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging

logger = logging.getLogger(__name__)

# Define a module-level default prompt template to avoid inline syntax issues
DEFAULT_PROMPT_TEMPLATE = """Given the lyrics: \"\"\"\n{lyrics}\n\"\"\". Extract any implied peace messages or anti-war sentiments, considering the context of 'The Cranberries - Zombie'. If no such message exists, state 'No explicit peace message found'.
Peace Message:"""


class LLMPeaceExtractor:
    _instance = None
    _initialized = False

    def __new__(cls, llm_config=None):
        if cls._instance is None:
            cls._instance = super(LLMPeaceExtractor, cls).__new__(cls)
        return cls._instance

    def __init__(self, llm_config=None):
        if not self._initialized:
            self.llm_config = llm_config if llm_config is not None else {}
            self.model = None
            self.tokenizer = None
            self._load_llm_model()
            LLMPeaceExtractor._initialized = True

    def _load_llm_model(self):
        model_path = self.llm_config.get('model_path', "Qwen/Qwen1.5-0.5B-Chat")
        logger.info(f"Loading LLM model from: {model_path}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForCausalLM.from_pretrained(model_path)
            logger.info("LLM model and tokenizer loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load LLM model or tokenizer from {model_path}: {e}")
            self.tokenizer = None
            self.model = None

    def extract_message(self, lyrics, prompt_template):
        """Core logic to extract implied peace messages using the loaded LLM.
        :param lyrics: The lyrics to analyze.
        :param prompt_template: The template for the prompt.
        """
        if self.tokenizer is None or self.model is None:
            logger.error("LLM model or tokenizer not loaded. Cannot extract message.")
            return f"[LLM Placeholder] LLM not available. Peace message from '{lyrics[:50]}...'"

        prompt = prompt_template.format(lyrics=lyrics)

        try:
            inputs = self.tokenizer(prompt, return_tensors='pt')
            outputs = self.model.generate(**inputs, max_new_tokens=100, num_return_sequences=1)

            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            extracted_message = generated_text.split("Peace Message:")[-1].strip()

            return extracted_message
        except Exception as e:
            logger.error(f"Error during LLM message generation: {e}. Returning placeholder.")
            return f"[LLM Placeholder] Peace message generation failed from '{lyrics[:50]}...'"

def extract_peace_message(lyrics, llm_config=None):
    """Module-level function to extract implied peace messages.
    Initializes LLMPeaceExtractor if not already done and calls its method.
    """
    logger.info(f"Analyzing lyrics for peace messages: {lyrics[:50]}...")

    extractor = LLMPeaceExtractor(llm_config)

    current_llm_config = llm_config if llm_config is not None else {}
    prompt_template = current_llm_config.get('prompt_template', DEFAULT_PROMPT_TEMPLATE)

    return extractor.extract_message(lyrics, prompt_template)

def ethical_filter(message, ethical_keywords=None):
    """Applies ethical filtering to the extracted peace message.
    :param ethical_keywords: List of keywords to filter for unethical content.
    """
    logger.info(f"Applying ethical filtering to: '{message[:50]}...' ")
    keywords_to_check = ethical_keywords if ethical_keywords is not None else ["violence", "hate"]

    for keyword in keywords_to_check:
        if keyword.lower() in message.lower():
            return f"[Filtered] Message contains unethical content related to '{keyword}'."
    return message
