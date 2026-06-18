import logging
from config import Config
from llm import generate_json
from intent import extract_intent

print(extract_intent("gravity"))
