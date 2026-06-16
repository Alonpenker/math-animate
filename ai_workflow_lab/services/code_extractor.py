from langchain_core.messages import BaseMessage


def extract_code(response: BaseMessage) -> str:
    content = response.content
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text_parts = [
            block["text"]
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        text = "".join(text_parts)
    else:
        raise ValueError(f"LLM returned non-text response content: {type(content).__name__}")

    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped
