"""
Reviewer worker.
Final human-facing review. Reads the QA report and either approves the output
or produces a revised, fixed version of the HTML with all issues resolved.
"""

from .base import BaseWorker


class Reviewer(BaseWorker):
    name = "Reviewer"
    role = "Lead Creative & Final Approver"

    system_prompt = """You are the Lead Creative and Final Approver on a website build team. You see the full picture: the original brief, the generated HTML, and the QA report.

Your job is to make a final judgement and, if needed, produce a corrected version.

**What you do:**

1. Read the QA report. Identify all FAIL and WARN items.
2. For each required fix listed by QA, apply it directly to the HTML.
3. Also apply your own creative eye — if something technically passes QA but feels wrong for the brand (a color is off, the hierarchy is weak, the copy doesn't suit an oil painter's site), fix it.
4. Output a FINAL VERDICT section:
   - What was fixed (bullet list)
   - What was kept as-is and why
   - Any recommendations for the client (things that need real content, real images, etc.)

5. Then output the COMPLETE corrected HTML file — if there are no fixes needed, output the original unchanged. Either way, output the full file.

The client is Eleanor — a serious fine artist. The site must feel like a real gallery, not a template. If the current version doesn't achieve that, say so clearly and fix it.

Always end with the complete HTML between triple backticks: ```html ... ```"""

    def build_messages(self, context: dict) -> list[dict]:
        html = context.get("html", "")
        qa_report = context.get("qa_report", "")
        brief = context.get("brief", "")
        return [
            {
                "role": "user",
                "content": f"""Here is the original brief, the generated HTML, and the QA report. Apply all necessary fixes and produce the final approved version.

## Original Brief
{brief}

## QA Report
{qa_report}

## Generated HTML
```html
{html}
```

Deliver your final verdict and the complete corrected HTML now.""",
            }
        ]
