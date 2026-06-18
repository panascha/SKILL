---
name: kku-intelsphere
description: |
  ใช้ skill นี้ทุกครั้งที่ต้องการ implement หรือใช้งาน KKU IntelSphere API ทั้งใน Python และ TypeScript
  Trigger เมื่อ user พูดถึง:
  - "KKU IntelSphere", "KKU API", "gen.ai.kku.ac.th"
  - ต้องการเรียก LLM ผ่าน KKU platform
  - ต้องการ boilerplate code สำหรับ KKU API ทั้ง Python/TypeScript
  - ถามถึง model ที่ available ใน KKU IntelSphere
  - ถามถึง quota หรือ rate limit ของ KKU platform
  - ต้องการ setup client หรือ wrapper สำหรับ KKU IntelSphere ใน project ของตัวเอง
  ห้าม undertrigger: ถ้า user mention KKU หรือ IntelSphere ในบริบทที่เกี่ยวกับ AI/LLM ให้ใช้ skill นี้เสมอ
---

# KKU IntelSphere API Skill

KKU IntelSphere เป็น AI API platform ของ มหาวิทยาลัยขอนแก่น (KKU) ที่รองรับ format เดียวกับ OpenAI API ทำให้ใช้ OpenAI SDK ได้โดยตรง

## Key Configuration

| Parameter | Value |
|-----------|-------|
| `base_url` | `https://gen.ai.kku.ac.th/api/v1` |
| `api_key`  | ดูได้จากหน้า platform (รูปแบบ `sk_...`) |

> **Best practice:** เก็บ API key ใน environment variable เสมอ — ห้าม hardcode ลงใน source code

---

## Python

### ติดตั้ง
```bash
pip install openai
```

### ตัวอย่าง Basic (Non-streaming)
```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("KKU_API_KEY"),
    base_url="https://gen.ai.kku.ac.th/api/v1"
)

response = client.chat.completions.create(
    model="gemini-2.5-flash",   # ดู models.md สำหรับรายการทั้งหมด
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello!"}
    ],
    stream=False
)

print(response.choices[0].message.content)
```

### ตัวอย่าง Streaming
```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("KKU_API_KEY"),
    base_url="https://gen.ai.kku.ac.th/api/v1"
)

stream = client.chat.completions.create(
    model="gemini-2.5-flash",
    messages=[{"role": "user", "content": "Write a short poem"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
```

### ตัวอย่าง Reusable Client Helper
```python
# kku_client.py
import os
from openai import OpenAI

def get_client() -> OpenAI:
    """Return a configured KKU IntelSphere client."""
    api_key = os.environ.get("KKU_API_KEY")
    if not api_key:
        raise ValueError("KKU_API_KEY environment variable is not set")
    return OpenAI(
        api_key=api_key,
        base_url="https://gen.ai.kku.ac.th/api/v1"
    )

def chat(messages: list[dict], model: str = "gemini-2.5-flash", **kwargs) -> str:
    """Simple wrapper — returns the assistant reply as a string."""
    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        **kwargs
    )
    return response.choices[0].message.content
```

### ตัวอย่าง Flask integration (สำหรับ Lecture Pipeline หรือ web app)
```python
# ใน Flask app
from kku_client import get_client

client = get_client()

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    response = client.chat.completions.create(
        model=data.get("model", "gemini-2.5-flash"),
        messages=data["messages"]
    )
    return {"reply": response.choices[0].message.content}
```

---

## TypeScript

### ติดตั้ง
```bash
npm install openai
# หรือ
yarn add openai
```

### ตัวอย่าง Basic (Non-streaming)
```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://gen.ai.kku.ac.th/api/v1",
  apiKey: process.env.KKU_API_KEY,
});

async function main() {
  const completion = await client.chat.completions.create({
    model: "gemini-2.5-flash",   // ดู models.md สำหรับรายการทั้งหมด
    messages: [
      { role: "system", content: "You are a helpful assistant" },
      { role: "user", content: "Hello!" },
    ],
    stream: false,
  });

  console.log(completion.choices[0].message.content);
}

main();
```

### ตัวอย่าง Streaming
```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://gen.ai.kku.ac.th/api/v1",
  apiKey: process.env.KKU_API_KEY,
});

async function streamChat() {
  const stream = await client.chat.completions.create({
    model: "gemini-2.5-flash",
    messages: [{ role: "user", content: "Write a short poem" }],
    stream: true,
  });

  for await (const chunk of stream) {
    const delta = chunk.choices[0]?.delta?.content;
    if (delta) process.stdout.write(delta);
  }
  console.log();
}

streamChat();
```

### ตัวอย่าง Reusable Client Helper (TypeScript module)
```typescript
// kkuClient.ts
import OpenAI from "openai";

let _client: OpenAI | null = null;

export function getClient(): OpenAI {
  if (!_client) {
    const apiKey = process.env.KKU_API_KEY;
    if (!apiKey) throw new Error("KKU_API_KEY environment variable is not set");
    _client = new OpenAI({
      baseURL: "https://gen.ai.kku.ac.th/api/v1",
      apiKey,
    });
  }
  return _client;
}

export async function chat(
  messages: OpenAI.Chat.ChatCompletionMessageParam[],
  model = "gemini-2.5-flash"
): Promise<string> {
  const client = getClient();
  const response = await client.chat.completions.create({ model, messages });
  return response.choices[0].message.content ?? "";
}
```

### ตัวอย่าง Browser / Frontend (dangerouslyAllowBrowser)
```typescript
// ⚠️  ใช้เฉพาะ dev/prototype เท่านั้น — ไม่ควร expose API key ใน production browser
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://gen.ai.kku.ac.th/api/v1",
  apiKey: import.meta.env.VITE_KKU_API_KEY,   // Vite example
  dangerouslyAllowBrowser: true,
});
```

---

## Environment Variables Setup

**.env file**
```env
KKU_API_KEY=sk_TXplgUt...YVdkoCnBFT
```

**Python (python-dotenv)**
```bash
pip install python-dotenv
```
```python
from dotenv import load_dotenv
load_dotenv()   # โหลด .env ก่อนสร้าง client
```

**Node.js / TypeScript**
```bash
npm install dotenv
```
```typescript
import "dotenv/config";   // ต้อง import ก่อนทุก import อื่นที่ใช้ env
```

---

## เลือก Model

ดูรายการ model ทั้งหมดและ quota ใน [`references/models-and-quota.md`](references/models-and-quota.md)

---

## Error Handling Pattern

```python
# Python
from openai import APIError, AuthenticationError, RateLimitError

try:
    response = client.chat.completions.create(...)
except AuthenticationError:
    print("API key ไม่ถูกต้อง — ตรวจสอบ KKU_API_KEY")
except RateLimitError:
    print("เกิน quota ประจำวัน — รอพรุ่งนี้หรือเปลี่ยน model")
except APIError as e:
    print(f"API error: {e}")
```

```typescript
// TypeScript
import { AuthenticationError, RateLimitError, APIError } from "openai";

try {
  const response = await client.chat.completions.create(...);
} catch (e) {
  if (e instanceof AuthenticationError) {
    console.error("API key ไม่ถูกต้อง — ตรวจสอบ KKU_API_KEY");
  } else if (e instanceof RateLimitError) {
    console.error("เกิน quota ประจำวัน — รอพรุ่งนี้หรือเปลี่ยน model");
  } else if (e instanceof APIError) {
    console.error(`API error: ${e.message}`);
  }
}
```

# KKU IntelSphere — Models & Quota Reference

## Available Models

| Provider | Model ID |
|----------|----------|
| **Claude** | `claude-sonnet-4.6` |
| Claude | `claude-sonnet-4.5` |
| Claude | `claude-haiku-4.5` |
| Claude | `claude-sonnet-4` |
| Claude | `claude-3.7-sonnet` |
| **Deepseek** | `deepseek-v4-pro` |
| Deepseek | `deepseek-v4-flash` |
| Deepseek | `deepseek-v3.2` |
| Deepseek | `deepseek-v3.2-exp` |
| Deepseek | `deepseek-chat-v3.1` |
| **Gemini** | `gemini-3.5-flash` |
| Gemini | `gemini-3.1-pro-preview` |
| Gemini | `gemini-3.1-flash-lite` |
| Gemini | `gemini-3.1-flash-lite-preview` |
| Gemini | `gemini-3-flash-preview` |
| Gemini | `gemini-2.5-pro` |
| Gemini | `gemini-2.5-flash` ⭐ |
| Gemini | `gemini-2.5-flash-lite` |
| Gemini | `gemini-3-pro-preview` |
| **Meta AI** | `llama-4-maverick` |
| Meta AI | `llama-4-scout` |
| **Mistral** | `mistral-small-2603` |
| Mistral | `mistral-large-2512` |
| Mistral | `mistral-medium-3` |
| Mistral | `codestral-2508` |
| Mistral | `devstral-medium` |
| Mistral | `codestral-2501` |
| **Nova (AWS)** | `nova-2-lite-v1` |
| Nova (AWS) | `nova-pro-v1` |
| **OpenAI** | `gpt-5.4` |
| OpenAI | `gpt-5.4-mini` |
| OpenAI | `gpt-5.4-nano` |
| OpenAI | `gpt-5.2` |
| OpenAI | `gpt-5.1` |
| OpenAI | `gpt-5.1-codex` |
| OpenAI | `gpt-5` |
| OpenAI | `gpt-5-mini` |
| OpenAI | `gpt-5-nano` |
| OpenAI | `gpt-5.5` |
| **Qwen** | `qwen3.7-max` |
| Qwen | `qwen3.6-flash` |
| Qwen | `qwen3.5-9b` |
| Qwen | `qwen3-235b-a22b-2507` |
| Qwen | `qwen3-next-80b-a3b-instruct` |
| Qwen | `qwen3-coder-flash` |
| Qwen | `qwen3-coder` |
| Qwen | `qwen3-vl-32b-instruct` |
| **xAI** | `grok-4.3` |
| xAI | `grok-4.1-fast` |
| xAI | `grok-4` |
| xAI | `grok-3` |

⭐ = recommended default

---

## Daily Quota (Tokens/Day)

| Provider | Total Tokens / Day |
|----------|-------------------|
| Gemini | 350,000 |
| Deepseek | **1,000,000** |
| Meta AI | 200,000 |
| Nova (AWS) | 200,000 |
| xAI | 200,000 |
| Perplexity | 200,000 |
| Qwen | 200,000 |
| Claude | 150,000 |
| OpenAI | 150,000 |
| Mistral | 150,000 |

> Quota คิดรวมจากการใช้บน KKU IntelSphere platform และ API รวมกัน (ต่อวัน)

---

## Model Selection Guide

### ตามประเภทงาน

| งาน | Model แนะนำ | เหตุผล |
|-----|-------------|--------|
| General chat / Q&A | `gemini-2.5-flash` | เร็ว, quota สูง, คุณภาพดี |
| Reasoning / Analysis | `gemini-2.5-pro` | ความสามารถ reasoning สูง |
| Coding | `deepseek-v4-pro` หรือ `codestral-2508` | specialized for code |
| Medical / Thai text | `claude-sonnet-4.6` | ภาษาไทยดี, instruction following ดี |
| High-volume / batch | `deepseek-v3.2` | quota 1M/day สูงที่สุด |
| Budget / lite tasks | `gemini-2.5-flash-lite` | เบา, ประหยัด quota |
| Vision / multimodal | `qwen3-vl-32b-instruct` | รองรับ image input |