# 🧠 AcmeDesk — Customer Support That Remembers

> A customer-support agent that doesn't just remember what happened — it remembers what was tried, what worked, what failed, and uses that experience to decide what to do next.

AcmeDesk is a support-agent prototype built around **persistent experience**.

It uses **Hindsight** as a memory layer and **Groq-powered LLM reasoning** to give the agent access to two kinds of long-term experience:

- **Private customer history** — what happened to this customer before, what they tried, what worked, what failed, and relevant preferences.
- **A shared support playbook** — anonymized outcomes from previous cases that help the agent recognize patterns across customers.

The key idea is simple:

**Remembering the past is useful only if it changes what the agent does next.**

---

## Why AcmeDesk?

A typical support agent can answer a customer's message.

A better support agent can remember the customer.

But a support agent becomes much more useful when it can distinguish between:

- a solution that worked previously,
- a solution that has already been tried in the current incident,
- a solution that worked historically but has now failed again, and
- a solution that has repeatedly worked across similar cases.

AcmeDesk is designed around that distinction.

For example, if a customer says:

> "I turned off transfer compression like before, but the export is still stuck at 99%."

the agent should **not** simply recommend turning compression off again.

It knows that the previously successful fix has already been attempted during the current incident and did not solve the problem. The next response therefore moves toward gathering information instead of repeating the same step.

That is the behavior this project is built to demonstrate.

---

# How It Works

```text
                    Customer
                       │
                       ▼
                Current Issue
                       │
              ┌────────┴────────┐
              ▼                 ▼
     Customer Memory      Shared Playbook
       (private)            (anonymized)
              │                 │
              └────────┬────────┘
                       ▼
                Case Analysis
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Reuse        Try known    Gather info /
     past fix        playbook      escalate
          │            │            │
          └────────────┼────────────┘
                       ▼
               Customer Response
                       │
                       ▼
                Actual Outcome
                       │
                       ▼
              ┌────────┴────────┐
              ▼                 ▼
       Customer Memory     Shared Playbook
