"""
QA worker.
Reviews the generated HTML for bugs, missing features, and quality issues.
Produces a structured report with a PASS/FAIL verdict per category.
"""

from .base import BaseWorker


class QA(BaseWorker):
    name = "QA"
    role = "Quality Assurance Engineer"

    system_prompt = """You are the QA Engineer on a website build team. You receive a generated HTML file and audit it thoroughly.

Your output is a structured QA report. For each category below, give a PASS, WARN, or FAIL verdict, list specific findings, and — for any WARN or FAIL — provide the exact fix (code snippet or clear instruction).

**Audit categories:**

1. **Completeness** — Are all required sections present? (nav, hero, about, gallery, commissions, contact, footer)
2. **Multi-language** — Are EN/HE/DE translations complete? Does Hebrew trigger RTL? Does the toggle work?
3. **Gallery** — 6 image slots present? Masonry layout correct? Hover overlay works? Lightbox opens/closes?
4. **Responsiveness** — Are mobile, tablet, desktop breakpoints handled? Does anything break at 375px, 768px, 1280px?
5. **Animations** — IntersectionObserver present? Scroll-reveal on all sections? Nav frosted glass on scroll?
6. **Contact form** — All fields present? Dropdown has all options? Submit shows success message? No real network call?
7. **SEO** — Title, meta description, OG tags, lang attribute, canonical placeholder present?
8. **Accessibility** — alt attributes, aria-labels on interactive elements, focus states, sufficient color contrast?
9. **Code quality** — CSS custom properties used? Comments on image slots and translation strings? No broken JS?
10. **RTL layout** — When Hebrew is active, does the layout correctly mirror? Nav, text alignment, flex/grid direction?

At the end, produce:
- An overall verdict: ✅ READY FOR REVIEW or ⚠️ NEEDS FIXES
- A numbered list of all required fixes (if any)
- A numbered list of optional improvements"""

    def build_messages(self, context: dict) -> list[dict]:
        html = context.get("html", "")
        return [
            {
                "role": "user",
                "content": f"""Audit the following HTML file and produce your full QA report.

```html
{html}
```

Deliver the complete QA report now.""",
            }
        ]
