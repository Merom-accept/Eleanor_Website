"""
Orchestrator — runs the 5 workers in sequence to build Eleanor's website.

Usage:
    python orchestrator.py

Requires:
    ANTHROPIC_API_KEY set in environment.

Output:
    output/01_plan.md
    output/02_design.md
    output/03_index_draft.html
    output/04_qa_report.md
    output/index.html          ← final approved file
"""

import os
import re
from pathlib import Path
import anthropic

# Load .env if present
_env = Path(__file__).parent / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

from workers import Planner, Designer, Architect, QA, Reviewer

# ─── Project Brief ────────────────────────────────────────────────────────────

BRIEF = """
Create a single-file artist portfolio website (index.html) for an artist named Eleanor.

ABOUT THE ARTIST:
Eleanor creates hyper-realistic large and XL oil paintings on canvas. She also does
large-scale commissions: interior murals, exterior building facades, and billboards.
Sales are handled by phone — no e-commerce needed.

LANGUAGES:
The site must support English, Hebrew, and German. Hebrew is RTL.
A language toggle (EN / HE / DE) sits in the navigation.
All text is defined in a JS translations object — easy for a non-developer to update.

PAGES / SECTIONS (single page, anchor nav):
- Fixed navigation: logo ("Eleanor") + links to each section + language toggle
- Hero: her name large, tagline about hyper-realistic oil paintings at monumental scale, CTA to gallery
- About: artist bio, portrait image slot, decorative stats (scale, medium, years active, etc.)
- Gallery: masonry grid, 6 image slots with hover overlays (title + dimensions), lightbox on click
- Commissions: explains large-format work (canvas, murals, billboards, facades), feature list
- Contact: form with fields: name, email, interest dropdown (purchase / canvas commission / mural / billboard / other), message textarea
- Footer: name + copyright year (auto)

DESIGN DIRECTION — warm & earthy:
- Color palette: cream #F4EFE4, linen #EDE5D4, dark umber #2B200F, terracotta #B85C30, sienna #8B4220, gold #C9973A
- Typography: Cormorant Garant (display) + Crimson Pro (body) from Google Fonts
- Subtle grain texture overlay on the body
- Radial gradient warm light effects in hero and commission sections
- Smooth scroll-reveal animations on all sections (IntersectionObserver)
- Nav becomes frosted glass on scroll
- Gallery lightbox for full-size image view

TECHNICAL REQUIREMENTS:
- Pure HTML + CSS + vanilla JS — no frameworks, no build tools
- All images are placeholders (colored SVG gradients with dimension labels) — easy to swap
- Contact form: client-side only, show success message on submit
- Fully responsive (mobile, tablet, desktop)
- SEO-ready <head> with meta description and OG tag placeholders
- Clean, commented code so a non-developer can find image slots easily

FEEL:
Stylish, cool, and engaging. Should feel like a real gallery — not a template.
Dramatic and immersive. The paintings should feel monumental even as placeholders.
"""

# ─── Helpers ──────────────────────────────────────────────────────────────────

def save(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  → Saved: {path}")


def extract_html(text: str) -> str:
    """Pull the HTML file out of the model's response (between ```html ... ```)."""
    match = re.search(r"```html\s*([\s\S]*?)```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: if the whole response looks like HTML, return it as-is
    if text.strip().startswith("<!DOCTYPE") or text.strip().startswith("<html"):
        return text.strip()
    return text  # return raw if we can't find a clean block


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set.")

    client = anthropic.Anthropic(api_key=api_key)
    context = {"brief": BRIEF}

    # 1. Planner — interactive session with the user
    planner = Planner(client)
    plan = planner.run_interactive(context)
    context["plan"] = plan
    save("output/01_plan.md", plan)

    # 2. Designer
    designer = Designer(client)
    design = designer.run(context)
    context["design"] = design
    save("output/02_design.md", design)

    # 3. Architect — writes the HTML
    architect = Architect(client)
    architect_output = architect.run(context)
    html_draft = extract_html(architect_output)
    context["html"] = html_draft
    save("output/03_index_draft.html", html_draft)

    # 4. QA
    qa = QA(client)
    qa_report = qa.run(context)
    context["qa_report"] = qa_report
    save("output/04_qa_report.md", qa_report)

    # 5. Reviewer — applies fixes and outputs final HTML
    reviewer = Reviewer(client)
    reviewer_output = reviewer.run(context)
    final_html = extract_html(reviewer_output)
    save("output/index.html", final_html)

    # Also save reviewer notes (everything before the HTML block)
    notes = re.sub(r"```html[\s\S]*?```", "", reviewer_output, flags=re.IGNORECASE).strip()
    if notes:
        save("output/05_reviewer_notes.md", notes)

    print("\n✅ Pipeline complete.")
    print("   Final file: output/index.html")


if __name__ == "__main__":
    main()
