import os
from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, logger

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

def generate_diary_content(date_str, hours=8.0):
    """
    Uses an LLM API to generate a plausible daily diary entry 
    if the original account lacks detailed logs for a specific date.
    Returns: dict with 'work_summary' and 'learnings'
    """
    prompt = f"""
    You are an AI generating plausible daily internship log entries for an engineering intern.
    Date: {date_str}
    Hours worked: {hours}
    
    Task: Write a concise, professional work summary (under 1000 chars) and 
    a learnings/outcomes paragraph (under 1000 chars) that sound like a typical
    software engineering intern day (e.g., attending standups, reviewing PRs, bug fixing, learning a framework).
    
    Provide the response strictly in this exact format:
    SUMMARY: <your summary text>
    LEARNINGS: <your learnings text>
    """
    
    try:
        if HAS_OPENAI and OPENAI_API_KEY:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            text = response.choices[0].message.content
        
        elif HAS_ANTHROPIC and ANTHROPIC_API_KEY:
            client = Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text
        else:
            logger.warning("No LLM API keys configured. Using static fallback text.")
            return _generate_static_fallback(date_str, hours)

        # Basic text parsing to split SUMMARY and LEARNINGS
        summary_raw = text.split("LEARNINGS:")[0].replace("SUMMARY:", "").strip()
        learnings_raw = text.split("LEARNINGS:")[1].strip() if "LEARNINGS:" in text else "General documentation and onboarding reviews."
        
        return {
            "work_summary": summary_raw,
            "learnings": learnings_raw
        }

    except Exception as e:
        logger.error(f"Failed generating AI content for {date_str}, falling back to static text. Error: {e}")
        return _generate_static_fallback(date_str, hours)

def _generate_static_fallback(date_str, hours):
    return {
        "work_summary": f"Continued ongoing development tasks and module integrations on {date_str}. Attended daily synchronization meeting.",
        "learnings": "Deepened understanding of project architecture and codebase navigation."
    }
