"""
Planner worker.
Runs an interactive back-and-forth session with the user to align on the plan,
then finalizes it when the user is satisfied.
"""

from .base import BaseWorker


class Planner(BaseWorker):
    name = "Planner"
    role = "Content & Structure Strategist"

    system_prompt = """You are the Planner on a website build team. You work collaboratively with the client before writing any plan.

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
When the user says something like "finalize", "looks good", "go ahead", or "done" — stop asking questions and output the complete structured plan. Signal this clearly with a header: ## FINAL PLAN

The final plan must include:
1. Section-by-section breakdown (content, purpose, key decisions)
2. Multi-language content outline (EN / HE / DE for each section)
3. User journey notes
4. Key constraints for the Designer and Architect
5. Must-haves vs nice-to-haves

Never output ## FINAL PLAN until the user explicitly signals they are done."""

    def run_interactive(self, context: dict) -> str:
        """
        Runs a live conversation in the terminal until the user finalizes.
        Returns the final plan text.
        """
        brief = context.get("brief", "")
        history = []

        print(f"\n{'='*60}")
        print(f"  {self.name.upper()} — {self.role}")
        print(f"  (Type your responses below. Say 'finalize' when ready.)")
        print(f"{'='*60}\n")

        # Seed the conversation with the brief
        history.append({
            "role": "user",
            "content": f"Here is the project brief. Start the discovery conversation — ask me your first questions.\n\n## Brief\n{brief}",
        })

        while True:
            # Stream the Planner's response
            full_response = ""
            with self.client.messages.stream(
                model=self.model,
                max_tokens=8000,
                thinking={"type": "adaptive"},
                system=self.system_prompt,
                messages=history,
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                        chunk = event.delta.text
                        full_response += chunk
                        print(chunk, end="", flush=True)

            print("\n")
            history.append({"role": "assistant", "content": full_response})

            # Check if the Planner already produced the final plan unprompted
            if "## FINAL PLAN" in full_response:
                break

            # Get user input
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[Session ended]")
                break

            if not user_input:
                continue

            history.append({"role": "user", "content": user_input})

            # If the user signals finalization, tell the Planner to wrap up
            finalize_signals = {"finalize", "done", "go ahead", "looks good", "proceed", "ok", "okay", "yes"}
            if any(sig in user_input.lower() for sig in finalize_signals):
                history.append({
                    "role": "user",
                    "content": "Good. Now output the ## FINAL PLAN.",
                })
                # Remove the duplicate before streaming (already appended above)
                # Actually remove the trigger message and replace with finalize instruction
                history.pop(-2)  # remove the user's short signal
                # Stream the final plan
                full_response = ""
                print("\n[Planner] Finalizing...\n")
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=16000,
                    thinking={"type": "adaptive"},
                    system=self.system_prompt,
                    messages=history,
                ) as stream:
                    for event in stream:
                        if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                            chunk = event.delta.text
                            full_response += chunk
                            print(chunk, end="", flush=True)
                print(f"\n\n[Planner done]\n")
                history.append({"role": "assistant", "content": full_response})
                break

        # Extract just the final plan section if present
        if "## FINAL PLAN" in full_response:
            return full_response[full_response.index("## FINAL PLAN"):]
        return full_response

    def build_messages(self, context: dict) -> list[dict]:
        brief = context.get("brief", "")
        return [
            {
                "role": "user",
                "content": f"Here is the project brief. Produce the full content & structure plan.\n\n## Project Brief\n{brief}\n\nDeliver the complete plan now.",
            }
        ]
