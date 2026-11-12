import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
c = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL"))

TOOL = [{"type": "function", "function": {
    "name": "get_sales_summary", "description": "Orders count and revenue.",
    "parameters": {"type": "object", "properties": {"note": {"type": "string"}}}}}]

for model in ["gemini-2.5-flash", "models/gemini-2.5-flash", "gemini-flash-latest", "gemini-3.5-flash"]:
    for use_tools in (False, True):
        kw = {"tools": TOOL} if use_tools else {}
        try:
            r = c.chat.completions.create(
                model=model, messages=[{"role": "user", "content": "Say hi"}], **kw)
            print("OK   ", model, "tools" if use_tools else "plain")
        except Exception as e:
            body = getattr(getattr(e, "response", None), "text", "")
            print("FAIL ", model, "tools" if use_tools else "plain", "->", str(e)[:150], body[:300])
            