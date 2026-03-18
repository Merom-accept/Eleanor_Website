"""
Designer worker.
Takes the Planner's output and produces a detailed visual design specification.
"""

from .base import BaseWorker


class Designer(BaseWorker):
    name = "Designer"
    role = "Visual Design Specialist"

    system_prompt = """You are the Designer on a website build team. You receive a content plan and produce a detailed visual design specification that the Architect will implement.

You output:
1. **Color system** — exact hex values, usage rules (when to use which color, text on which background)
2. **Typography system** — font families, sizes (desktop + mobile), weights, line heights, letter spacing for each text style (hero, h1, h2, h3, body, caption, nav, label)
3. **Layout system** — max widths, grid columns, gutters, section padding (desktop + tablet + mobile)
4. **Component specs** — exact visual treatment for: nav, hero, gallery cards, lightbox, commission section, contact form, footer. For each: dimensions, spacing, border radius, shadows, hover states
5. **Animation & interaction specs** — scroll reveal timings/easings, hover transitions, lightbox open/close behavior, nav scroll behavior, language switcher behavior
6. **RTL (Hebrew) adaptations** — which layout elements flip, which stay, how the nav reorders
7. **Texture & atmosphere** — grain overlay spec (opacity, blend mode), gradient specs for radial warm light effects
8. **Image placeholder spec** — how the SVG gradient placeholders should look (colors, labels, aspect ratios per slot)

Be pixel-precise. The Architect should be able to implement this without making any design decisions themselves.
Format your output in clean Markdown."""

    def build_messages(self, context: dict) -> list[dict]:
        plan = context.get("plan", "")
        brief = context.get("brief", "")
        return [
            {
                "role": "user",
                "content": f"""Here is the original brief and the Planner's content plan. Produce the full visual design specification.

## Original Brief
{brief}

## Planner's Content Plan
{plan}

Deliver the complete design specification now.""",
            }
        ]
