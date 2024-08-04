import json
import logging


def amend_partial_json_resp(claude_response: str):
    if "```json" in claude_response:
        start = claude_response.index("```json")
        claude_response = claude_response[start + len("```json"):]
    end_idx = claude_response.rindex("},")
    claude_response = claude_response[:end_idx + 1]  # include closing curley brackets
    claude_response += "]}"
    return claude_response


def extract_json_from_prompt_text_block(text_block: str):
    res = {}
    if "```json" in text_block:
        start = text_block.index("```json")
        end = text_block.rindex("```")
        if end <= start:
            logging.error("detected an invalid json annotation in text block")
            return {}
        text_block = text_block[start + len("```json"):end]
    try:
        res = json.loads(text_block)
    except json.JSONDecodeError as e:
        logging.error("could not decode json from string with error: %s", e)
    return res
