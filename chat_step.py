"""
Single-step runner for the Planner conversation.
Usage:
    python chat_step.py                        # first turn (seeds with brief)
    python chat_step.py "user message here"    # subsequent turns
    python chat_step.py --finalize             # ask Planner to output final plan
    python chat_step.py --show-plan            # print just the final plan from history
"""

import sys
import json
import os
import anthropic

HISTORY_FILE = "output/.planner_history.json"
BRIEF_FILE = "orchestrator.py"  # we read BRIEF from here

# ── Read the brief from orchestrator.py ───────────────────────────────────────
def get_brief() -> str:
    with open(BRIEF_FILE, encoding="utf-8") as f:
        src = f.read()
    start = src.index('BRIEF = """') + len('BRIEF = """')
    end = src.index('"""', start)
    return src[start:end].strip()

SYSTEM_PROMPT = """You are the Planner on a website build team. You work collaboratively with the client before writing any plan.

Your job has two phases:

PHASE 1 — DISCOVERY (conversation)
Ask focused, opinionated questions to fill gaps in the brief. Don't ask everything at once — ask the 2-3 most important things, listen, then follow up. You're trying to understand:
- Tone and feel (what does "stylish and cool" mean to this client specifically?)
- Content priorities (what matters most — gallery? commissions? biography?)
- Gallery decisions (how many works to show? any specific paintings to highlight?)
- Audience (who is visiting — collectors, interior designers, art lovers, press?)
- Anything the brief leaves ambiguous

Be direct and conversational. Share your own instincts and opinions — you're a professional, not just a note-taker. Push back if something seems off.

PHASE 2 — FINALIZATION
When asked to finalize — output the complete structured plan under the header ## FINAL PLAN

The final plan must include:
1. Section-by-section breakdown (content, purpose, key decisions)
2. Multi-language content outline (EN / HE / DE for each section)
3. User journey notes
4. Key constraints for the Designer and Architect
5. Must-haves vs nice-to-haves

Never output ## FINAL PLAN until explicitly asked."""

def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history: list):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def run_step(history: list) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    full = ""
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=history,
    ) as stream:
        for event in stream:
            if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                full += event.delta.text
                print(event.delta.text, end="", flush=True)
    print()
    return full

def main():
    args = sys.argv[1:]
    history = load_history()

    if "--show-plan" in args:
        # Print the last assistant message (should be the final plan)
        for msg in reversed(history):
            if msg["role"] == "assistant" and "## FINAL PLAN" in msg["content"]:
                idx = msg["content"].index("## FINAL PLAN")
                print(msg["content"][idx:])
                return
        print("No final plan found in history yet.")
        return

    if not history:
        # First turn — seed with brief
        brief = get_brief()
        history.append({
            "role": "user",
            "content": f"Here is the project brief. Start the discovery conversation — ask me your first questions.\n\n## Brief\n{brief}"
        })

    elif "--finalize" in args:
        history.append({
            "role": "user",
            "content": "Good. Now output the ## FINAL PLAN based on everything we've discussed."
        })

    elif args:
        user_message = " ".join(args)
        history.append({"role": "user", "content": user_message})

    response = run_step(history)
    history.append({"role": "assistant", "content": response})
    save_history(history)

if __name__ == "__main__":
    main()
