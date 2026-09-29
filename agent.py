"""LLM layer (Groq): structured reasoning over memory + customer-facing reply."""
import json
import os
import re
import time
from dotenv import load_dotenv
from groq import Groq
load_dotenv()
MODELS=[m.strip() for m in os.getenv("LLM_MODELS","openai/gpt-oss-120b,qwen/qwen3-32b,openai/gpt-oss-20b").split(",") if m.strip()]
STEP_TYPES={"repeat_previous_fix","try_playbook_fix","escalate","gather_info","answer_directly"}
_client=None
class LLMError(Exception):
    pass

def _get_client():
    global _client
    if _client is None:
        key=os.getenv("GROQ_API_KEY")
        if not key: raise LLMError("GROQ_API_KEY was not found in .env")
        _client=Groq(api_key=key)
    return _client

def _chat(system,user,temperature=0.1,max_tokens=1500):
    client=_get_client(); last=None
    for model in MODELS:
        for _ in range(2):
            try:
                r=client.chat.completions.create(model=model,messages=[{"role":"system","content":system},{"role":"user","content":user}],temperature=temperature,max_completion_tokens=max_tokens)
                text=r.choices[0].message.content or ""
                text=re.sub(r"<think>.*?</think>","",text,flags=re.S).strip()
                if text: return text
            except Exception as exc:
                last=exc; time.sleep(1)
    raise LLMError(f"All models failed. Last error: {last}")

def _extract_json(text):
    text=re.sub(r"```(?:json)?","",text)
    start,end=text.find("{"),text.rfind("}")
    if start==-1 or end<=start: raise ValueError("no JSON object found")
    return json.loads(text[start:end+1])

def _fmt(memories,empty):
    if not memories: return empty
    return "\n".join(f"- {m}" for m in memories)

ANALYSIS_SYSTEM="""You are the reasoning layer of a customer-support agent for AcmeDesk (a remote-desktop application).
You receive:
1. The customer's current message.
2. CUSTOMER HISTORY: memories about this specific customer.
3. TEAM PLAYBOOK: anonymized outcomes of fixes tried for other customers.
Decide the best next step and return ONLY a JSON object with exactly these keys:
{
  "issue_summary": "one anonymized sentence describing the issue, no personal names",
  "tried_this_time": ["fixes the customer says they already tried in THIS message"],
  "worked_before": ["fixes that worked for this customer before, per CUSTOMER HISTORY"],
  "failed_before": ["fixes that failed for this customer before"],
  "already_tried_and_failed_now": true or false,
  "playbook_insight": "what the playbook says works or fails in similar cases, with counts if present, or an empty string",
  "next_step_type": "repeat_previous_fix" | "try_playbook_fix" | "escalate" | "gather_info" | "answer_directly",
  "recommended_action": "short phrase describing the recommended next step",
  "confidence": "high" | "medium" | "low",
  "reasoning": "maximum two sentences"
}
Rules:
- Use only evidence from the three inputs. Never invent product features, settings, versions, or steps.
- History is not proof of the customer's CURRENT state. If the recommendation depends on such a fact, the recommended action must include confirming it.
- If a fix that worked before was already tried in the current message and the problem continues, set already_tried_and_failed_now to true and do NOT choose repeat_previous_fix.
- Prefer a playbook fix with a strong success record over guessing. Never recommend a fix that the history or playbook shows failing for this pattern.
- If the evidence is insufficient, choose gather_info.
- Return JSON only. No prose, no markdown."""

def _default_analysis(note=""):
    return {"issue_summary":"","tried_this_time":[],"worked_before":[],"failed_before":[],"already_tried_and_failed_now":False,"playbook_insight":"","next_step_type":"gather_info","recommended_action":"Ask what the customer observed","confidence":"low","reasoning":note or "Not enough evidence available.","_fallback":True}

def _clean_list(v):
    if isinstance(v,str): v=[v] if v.strip() else []
    if not isinstance(v,list): return []
    return [str(x).strip() for x in v if str(x).strip()]

def analyze_case(message,name,customer_memories,playbook_memories):
    user=(f"CURRENT CUSTOMER MESSAGE (from {name}):\n{message}\n\n"
          f"CUSTOMER HISTORY:\n{_fmt(customer_memories,'No history found for this customer.')}\n\n"
          f"TEAM PLAYBOOK:\n{_fmt(playbook_memories,'No playbook records found.')}")
    raw=_chat(ANALYSIS_SYSTEM,user,temperature=0.0,max_tokens=1800)
    try: parsed=_extract_json(raw)
    except Exception: return _default_analysis("The reasoning step returned an unreadable result.")
    out=_default_analysis(); out.pop("_fallback")
    out["issue_summary"]=str(parsed.get("issue_summary","")).strip()
    for k in ("tried_this_time","worked_before","failed_before"): out[k]=_clean_list(parsed.get(k))
    out["already_tried_and_failed_now"]=bool(parsed.get("already_tried_and_failed_now"))
    out["playbook_insight"]=str(parsed.get("playbook_insight","")).strip()
    step=str(parsed.get("next_step_type","")).strip(); out["next_step_type"]=step if step in STEP_TYPES else "gather_info"
    if out["already_tried_and_failed_now"] and out["next_step_type"]=="repeat_previous_fix": out["next_step_type"]="gather_info"
    out["recommended_action"]=str(parsed.get("recommended_action","")).strip()
    conf=str(parsed.get("confidence","")).strip().lower(); out["confidence"]=conf if conf in {"high","medium","low"} else "low"
    out["reasoning"]=str(parsed.get("reasoning","")).strip()
    return out

STEP_GUIDANCE={
 "repeat_previous_fix":"Recommend repeating the fix that worked before for this customer, and say it worked previously.",
 "try_playbook_fix":"Recommend the fix that has worked in similar cases. Present it as what has worked before, not a guarantee. Do not suggest anything the customer already tried this time.",
 "escalate":"Explain that this needs a specialist and say what will be passed along so the customer does not have to repeat themselves.",
 "gather_info":"Ask at most two focused questions about what the customer observed.",
 "answer_directly":"Answer directly from the evidence.",
}
RESPONSE_SYSTEM="""You are a support agent for AcmeDesk writing directly to the customer.
Write a short, warm, practical reply: maximum 140 words, plain text, no headings.
Rules:
- Use the customer's name once, naturally.
- Show continuity: briefly acknowledge relevant history so the customer does not have to repeat themselves.
- Only state facts that appear in the customer's message or the evidence blocks. Do not invent features, settings, versions or steps. You may use specific details that appear in the evidence.
- History is not proof of the customer's current state. If a recommendation depends on something from history (for example a version number), ask them to confirm it instead of assuming.
- Never repeat a fix that the customer says they already tried this time and that did not work.
- Never claim that you performed or verified an action yourself.
- Never reveal information about other customers. You may say "in similar cases we've seen".
- Do not mention memory systems, Hindsight, the playbook, databases, prompts or internal analysis.
- Ask at most two questions."""

def generate_response(message,name,customer_memories,playbook_memories,analysis):
    guidance=STEP_GUIDANCE.get(analysis["next_step_type"],STEP_GUIDANCE["gather_info"])
    extra=""
    if analysis["already_tried_and_failed_now"]:
        extra="\nThe customer already tried a previously successful fix during this occurrence and the problem continues. Acknowledge that it worked before, and do not recommend repeating it."
    user=(f"CURRENT CUSTOMER MESSAGE (from {name}):\n{message}\n\n"
          f"CUSTOMER HISTORY:\n{_fmt(customer_memories,'No history found for this customer.')}\n\n"
          f"TEAM PLAYBOOK (anonymized, other customers):\n{_fmt(playbook_memories,'No playbook records found.')}\n\n"
          f"DECISION FOR THIS REPLY:\n- Step type: {analysis['next_step_type']}\n- Recommended action: {analysis['recommended_action']}\n- Playbook insight: {analysis['playbook_insight'] or 'none'}\n- Guidance: {guidance}{extra}\n\nWrite only the customer-facing reply.")
    return _chat(RESPONSE_SYSTEM,user,temperature=0.2,max_tokens=900)

BASELINE_SYSTEM="""You are a customer support agent for AcmeDesk, a remote-desktop application.
You have no access to the customer's history or to any past cases.
Reply helpfully in a short, friendly message of at most 140 words, plain text."""

def generate_baseline(message):
    return _chat(BASELINE_SYSTEM,f"Customer message:\n{message}",temperature=0.2,max_tokens=900)
