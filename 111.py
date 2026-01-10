import openai, json, time, pandas as pd
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

prompt = """你是一名代码审计专家。  
下面给出 Java 函数源码，请判断是否存在安全漏洞（如注入、越界、XXE 等）。  
按 JSON 回答：{"vuln": true/false, "type": "OWASP Top10 类别", "reason": "一句话原因", "patch": "给出修改后代码片段"}  """

results = []
for src in df['code']:
    rsp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt + src}],
        temperature=0
    )
    results.append(json.loads(rsp.choices[0].message.content))