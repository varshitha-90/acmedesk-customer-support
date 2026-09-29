"""AcmeDesk support agent with persistent memory (Hindsight) - Streamlit UI."""
import concurrent.futures as cf
import time

import streamlit as st

import agent
import data
import memory

st.set_page_config(page_title="AcmeDesk - support agent with memory", page_icon="🧠", layout="wide")

NEW = "__new__"
STEP_LABELS = {
    "repeat_previous_fix": "Repeat a fix that worked",
    "try_playbook_fix": "Try a playbook fix",
    "escalate": "Escalate",
    "gather_info": "Gather more info",
    "answer_directly": "Answer directly",
}

for key, default in {
    "result": None,
    "saved_msg": None,
    "timeline": [],
    "briefs": {},
    "message_input": "",
    "new_name": "",
}.items():
    st.session_state.setdefault(key, default)


def load_demo(customer, message, new_name=""):
    st.session_state["customer_choice"] = customer
    st.session_state["message_input"] = message
    if new_name:
        st.session_state["new_name"] = new_name
    st.session_state["result"] = None
    st.session_state["saved_msg"] = None


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("Customer")
    options = list(data.CUSTOMERS) + [NEW]
    choice = st.selectbox(
        "Who is contacting support?",
        options,
        key="customer_choice",
        format_func=lambda k: "➕ New customer"
        if k == NEW
        else f'{data.CUSTOMERS[k]["name"]} ({data.CUSTOMERS[k]["plan"]})',
    )
    if choice == NEW:
        st.text_input("Customer name", key="new_name", placeholder="e.g. Meera Nair")

    st.divider()
    st.subheader("Demo scenarios")
    for i, s in enumerate(data.DEMO_SCENARIOS):
        st.button(
            s["label"],
            key=f"demo_{i}",
            on_click=load_demo,
            args=(s["customer"], s["message"], s.get("new_name", "")),
            use_container_width=True,
        )
    st.caption("All customers and tickets are synthetic demo data for a fictional product.")


def resolve_customer():
    if choice == NEW:
        name = (st.session_state.get("new_name") or "").strip()
        return None if not name else ("new-" + memory.slugify(name), name)
    return choice, data.CUSTOMERS[choice]["name"]


# ------------------------------------------------------------------- header
st.title("🧠 AcmeDesk support agent that remembers")
st.write(
    "Every customer has their own Hindsight memory bank, and a shared playbook bank "
    "learns which fixes actually work across customers. Ask the same question with "
    "and without memory and compare."
)

customer = resolve_customer()

# ----------------------------------------------------------- customer brief
if customer:
    cid, cname = customer
    if st.button(f"🧾 Customer brief for {cname} (Hindsight reflect)"):
        with st.spinner("Reflecting over this customer's memories..."):
            text, err = memory.reflect(
                memory.customer_bank_id(cid),
                "Summarize this customer's support history: recurring issues, which fixes "
                "worked, which failed, and how they prefer to be helped. Be brief.",
            )
        st.session_state.briefs[cid] = (text, err)
    if cid in st.session_state.briefs:
        text, err = st.session_state.briefs[cid]
        if text:
            st.info(text)
        else:
            st.caption(f"No brief available yet ({err or 'no history for this customer'}).")

st.divider()

# ------------------------------------------------------------------- input
message = st.text_area(
    "Customer message",
    key="message_input",
    height=110,
    placeholder="Example: My AcmeDesk connection is dropping again.",
)


def run_support(cid, name, msg):
    bank = memory.customer_bank_id(cid)
    with cf.ThreadPoolExecutor(max_workers=1) as ex:
        baseline_future = ex.submit(agent.generate_baseline, msg)  # LLM only, no memory
        cust_mem, cust_err = memory.recall(bank, msg)
        play_mem, play_err = memory.recall(memory.PLAYBOOK_BANK, msg)
        analysis = agent.analyze_case(msg, name, cust_mem, play_mem)
        response = agent.generate_response(msg, name, cust_mem, play_mem, analysis)
        try:
            baseline, baseline_err = baseline_future.result(), None
        except Exception as exc:  # noqa: BLE001
            baseline, baseline_err = None, str(exc)
    return {
        "id": int(time.time() * 1000),
        "cid": cid,
        "name": name,
        "message": msg,
        "cust_mem": cust_mem,
        "play_mem": play_mem,
        "cust_err": cust_err,
        "play_err": play_err,
        "analysis": analysis,
        "response": response,
        "baseline": baseline,
        "baseline_err": baseline_err,
    }


if st.button("Get support response", type="primary"):
    msg = message.strip()
    if not msg:
        st.warning("Please enter a customer message.")
    elif customer is None:
        st.warning("Please enter the new customer's name in the sidebar.")
    else:
        try:
            with st.spinner("Recalling history, reasoning, and writing a reply..."):
                res = run_support(customer[0], customer[1], msg)
            st.session_state.result = res
            st.session_state.saved_msg = None
            st.session_state.timeline.append(
                {
                    "customer": res["name"],
                    "customer memories": len(res["cust_mem"]),
                    "playbook records": len(res["play_mem"]),
                    "decision": STEP_LABELS.get(res["analysis"]["next_step_type"], "-"),
                }
            )
        except agent.LLMError as exc:
            st.error(f"The language model is unavailable right now: {exc}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Something went wrong: {exc}")

# ----------------------------------------------------------------- results
res = st.session_state.result
if res:
    a = res["analysis"]

    if res["cust_err"] or res["play_err"]:
        st.warning(
            "Memory service problem - the agent answered with whatever it could recall. "
            f"Details: {res['cust_err'] or ''} {res['play_err'] or ''}"
        )

    m1, m2, m3 = st.columns(3)
    m1.metric("Customer memories recalled", len(res["cust_mem"]))
    m2.metric("Playbook records recalled", len(res["play_mem"]))
    m3.metric("Agent decision", STEP_LABELS.get(a["next_step_type"], "-"))

    left, right = st.columns(2)
    with left:
        st.subheader("Without memory")
        st.caption("Same model, no history, no playbook")
        with st.container(border=True):
            if res["baseline"]:
                st.write(res["baseline"])
            else:
                st.write(f"Baseline unavailable: {res['baseline_err']}")
    with right:
        st.subheader("With Hindsight memory")
        st.caption("Customer history + shared playbook")
        with st.container(border=True):
            st.write(res["response"])

    with st.expander("🔎 Agent reasoning", expanded=True):
        if a.get("_fallback"):
            st.caption("Reasoning fell back to the safe default (gather more info).")
        if a["already_tried_and_failed_now"]:
            st.warning("A fix that worked before was already tried this time and failed. The agent will not repeat it.")
        st.markdown(f"**Issue:** {a['issue_summary'] or '-'}")
        st.markdown(f"**Tried this time:** {', '.join(a['tried_this_time']) or '-'}")
        st.markdown(f"**Worked before:** {', '.join(a['worked_before']) or '-'}")
        st.markdown(f"**Failed before:** {', '.join(a['failed_before']) or '-'}")
        st.markdown(f"**Playbook insight:** {a['playbook_insight'] or '-'}")
        st.markdown(f"**Decision:** {STEP_LABELS.get(a['next_step_type'], '-')} - {a['recommended_action'] or '-'}")
        st.markdown(f"**Confidence:** {a['confidence']}  \n**Why:** {a['reasoning'] or '-'}")

    with st.expander("🧠 Memory inspector (raw recall from Hindsight)"):
        t1, t2 = st.tabs([f"{res['name']}'s bank", "Shared playbook"])
        with t1:
            if res["cust_mem"]:
                for m in res["cust_mem"]:
                    st.markdown(f"- {m}")
            else:
                st.caption("No history yet for this customer.")
        with t2:
            if res["play_mem"]:
                for m in res["play_mem"]:
                    st.markdown(f"- {m}")
            else:
                st.caption("No playbook records matched.")

    # ------------------------------------------------------------- outcome
    st.divider()
    st.subheader("📌 Record what happened")
    rid = res["id"]
    outcome = st.radio(
        "Outcome",
        ["Resolved", "Not resolved", "Escalated to engineering"],
        horizontal=True,
        key=f"outcome_{rid}",
    )
    tried = st.text_input(
        "What did the customer actually try?",
        value=a["recommended_action"],
        key=f"tried_{rid}",
    )
    notes = st.text_input(
        "Notes (frustration, preferences, version, etc.)",
        key=f"notes_{rid}",
    )
    if st.button("Save to memory"):
        with st.spinner("Saving to the customer's bank and the shared playbook..."):
            errors = memory.save_outcome(
                res["cid"], res["name"], a["issue_summary"], res["message"], tried, outcome, notes
            )
        if errors:
            st.error("Could not save everything: " + " | ".join(errors))
            st.session_state.saved_msg = None
        else:
            st.session_state.saved_msg = (
                "Saved. Ask again to see the agent use this new experience."
            )
    if st.session_state.saved_msg:
        st.success(st.session_state.saved_msg)

# ---------------------------------------------------------------- timeline
if st.session_state.timeline:
    with st.expander("📈 This session: how the agent's context grows"):
        st.table(st.session_state.timeline)