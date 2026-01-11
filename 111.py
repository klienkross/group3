import openai, json, time, pandas as pd
from config import OPENAI_API_KEY
import os
from openai import OpenAI

openai.api_key = OPENAI_API_KEY, DEEPSEEK_API_KEY

prompt = """你是一名代码审计专家。  
下面给出 Java 函数源码，请判断是否存在安全漏洞（如注入、越界、XXE 等）。  
按 JSON 回答：{"vuln": true/false, "type": "OWASP Top10 类别", "reason": "一句话原因", "patch": "给出修改后代码片段"}  """
src = "URL='https://localhost:8443/benchmark/pathtraver-00/BenchmarkTest00001' tcName='BenchmarkTest00001' tcType='SERVLET'><cookie name='BenchmarkTest00001' value='FileName' />"


results = []
# for src in df['code']:
#     rsp = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[{"role": "user", "content": prompt + src}],
#         temperature=0
#     )
#     results.append(json.loads(rsp.choices[0].message.content))

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt + src}],
    temperature=0
    stream=False
)
print(response.choices[0].message.content)