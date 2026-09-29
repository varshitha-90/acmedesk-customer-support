"""Hindsight memory layer for AcmeDesk.

One private memory bank per customer + one anonymized shared playbook bank.
"""
import os
import re
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()
BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
PLAYBOOK_BANK = "acmedesk-playbook"
MAX_MEMORY_CHARS = 700
_client = None

def get_client():
    global _client
    if _client is None:
        key = os.getenv("HINDSIGHT_API_KEY")
        if not key:
            raise RuntimeError("HINDSIGHT_API_KEY was not found in .env")
        _client = Hindsight(base_url=BASE_URL, api_key=key)
    return _client

def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "unknown"

def customer_bank_id(customer_id):
    return f"acmedesk-customer-{customer_id}"

def _dedupe(texts):
    seen=[]
    for t in texts:
        t=(t or "").strip()
        if t and t not in seen:
            seen.append(t[:MAX_MEMORY_CHARS])
    return seen

def format_ticket(name,t):
    return (f"Support ticket for {name} on {t['when']:%Y-%m-%d}.\n"
            f"Issue reported: {t['issue']}\nFix attempted: {t['tried']}\n"
            f"Result: {t['result']}\nNotes: {t['notes']}")

def format_playbook(t):
    return (f"Anonymized resolution record from {t['when']:%Y-%m-%d}.\n"
            f"Issue pattern: {t['issue']}\nFix attempted: {t['tried']}\n"
            f"Result: {t['result']}\nNotes: {t['notes']}")

def ensure_bank(bank_id, mission=None):
    c=get_client()
    try:
        if mission:
            try: c.create_bank(bank_id=bank_id,name=bank_id,mission=mission)
            except TypeError: c.create_bank(bank_id=bank_id,name=bank_id,background=mission)
        else: c.create_bank(bank_id=bank_id,name=bank_id)
    except Exception: pass

def recall(bank_id,query,limit=8):
    try:
        result=get_client().recall(bank_id=bank_id,query=query)
        texts=[getattr(m,"text",None) for m in result.results]
        return _dedupe(texts)[:limit],None
    except Exception as exc:
        msg=f"{type(exc).__name__}: {exc}"
        if "404" in msg or "not found" in msg.lower(): return [],None
        return [],msg

def retain(bank_id,content,context,when=None):
    c=get_client(); last=None
    for attempt in range(3):
        try:
            if when is not None and attempt==0:
                try: return c.retain(bank_id=bank_id,content=content,context=context,timestamp=when)
                except TypeError: pass
            return c.retain(bank_id=bank_id,content=content,context=context)
        except Exception as exc:
            last=exc; time.sleep(1.5*(attempt+1))
    raise last

def reflect(bank_id,query):
    try:
        res=get_client().reflect(bank_id=bank_id,query=query)
        text=(getattr(res,"text",None) or "").strip()
        return (text or None),None
    except Exception as exc: return None,f"{type(exc).__name__}: {exc}"

def save_outcome(customer_id,name,issue_summary,message,tried,result,notes):
    now=datetime.now(timezone.utc); errors=[]
    ticket={"when":now,"issue":message,"tried":tried or "Not specified","result":result,"notes":notes or "None"}
    playbook={"when":now,"issue":issue_summary or "Unspecified issue","tried":tried or "Not specified","result":result,"notes":notes or "Single case."}
    try: retain(customer_bank_id(customer_id),format_ticket(name,ticket),"customer support ticket outcome",when=now)
    except Exception as exc: errors.append(f"customer memory: {exc}")
    try: retain(PLAYBOOK_BANK,format_playbook(playbook),"anonymized resolution record",when=now)
    except Exception as exc: errors.append(f"playbook memory: {exc}")
    return errors
