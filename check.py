import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
base = os.getenv("LLM_BASE_URL")
print("BASE URL:", repr(base))
print("MODEL   :", repr(os.getenv("LLM_MODEL")))

c = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=base)
try:
    for m in c.models.list():
        print(m.id)
except Exception as e:
    print("ERROR:", e)