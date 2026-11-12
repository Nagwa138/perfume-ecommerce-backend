import os, time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
c = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL"), timeout=40)
for model in ["gemini-flash-lite-latest", "gemini-3.8-flash"]:
    t = time.time()
    try:
        c.chat.completions.create(model=model, messages=[{"role": "user", "content": "Say hi"}])
        print(model, "OK in", round(time.time() - t, 1), "s")
    except Exception as e:
        print(model, "FAIL after", round(time.time() - t, 1), "s:", str(e)[:200])