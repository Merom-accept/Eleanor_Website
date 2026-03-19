# Eleanor Website — Project Status

Last updated: 2026-03-19

---

## What This Project Is

Single-file artist portfolio website for **Eleanor** — a hyper-realistic oil painter who works at large scale (canvas, murals, facades, billboards). Three languages: English, Hebrew (RTL), German. No e-commerce. Sales via phone/contact form.

---

## Pipeline Architecture

5 AI workers run in sequence via `orchestrator.py`:

```
Planner → Designer → Architect → QA → Reviewer
```

| Worker | File | Job |
|---|---|---|
| Planner | `workers/planner.py` | Content plan + multi-language outline |
| Designer | `workers/designer.py` | Visual design spec (colors, type, components) |
| Architect | `workers/architect.py` | Writes the actual HTML/CSS/JS |
| QA | `workers/qa.py` | Audits output, PASS/WARN/FAIL per category |
| Reviewer | `workers/reviewer.py` | Applies fixes, outputs final approved file |

Workers use `claude-opus-4-6` with adaptive thinking + streaming.
Planner runs interactively (chat) — others run headless.
API key: set in `.env` (see `.env.example`). Never committed.

---

## Key Decisions Made (Planner session)

| Topic | Decision |
|---|---|
| Gallery order | Randomized on every page load (JS Fisher-Yates shuffle) |
| Click tracking | GA4 `painting_click` events wired — activate by dropping gtag in `<head>` |
| Audience | Art galleries + large-scale commercial clients — unified by scale story |
| Commissions section | Lean — statement + 4 formats + CTA to contact. No pricing or process. |
| Hero | Typographic name dominant, full-bleed painting behind, bold tagline |
| Color scheme | Locked from brief — warm earthy palette, dark umber weighted heavily |
| Section rhythm | Dark hero → light gallery → light about → dark commissions → light contact → dark footer |

---

## Color Palette (locked)

| Name | Hex | Usage |
|---|---|---|
| Cream | `#F4EFE4` | Light section backgrounds |
| Linen | `#EDE5D4` | About section, secondary surfaces |
| Dark Umber | `#2B200F` | Dark sections, primary text on light |
| Terracotta | `#B85C30` | Primary CTAs, active states |
| Sienna | `#8B4220` | Hover on CTAs, secondary accents |
| Gold | `#C9973A` | Stat labels, hover highlights |

---

## Current State of index.html

**File:** `index.html` (root) + `output/index.html` (working copy)
**Status:** ✅ Final — all QA fixes applied by Reviewer

### What's in the file
- All 7 sections: nav, hero, gallery, about, commissions, contact, footer
- EN / HE / DE translations complete
- RTL support for Hebrew (logical CSS properties + `[dir="rtl"]` overrides)
- 6 painting slots — SVG gradient placeholders, randomized on load
- Lightbox with prev/next, counter, ESC/arrow keyboard nav
- GA4 click tracking hooks (fires even without GA loaded)
- IntersectionObserver scroll reveal on all sections + stagger
- Frosted glass nav on scroll
- Contact form — client-side only, shows success state on submit
- Grain texture overlay on body
- Warm radial glows in hero + commissions

### Image slots (all need real images)
| Slot | Painting | Dimensions | Variable |
|---|---|---|---|
| Hero bg | — | full bleed | Replace SVG in `.hero-bg` |
| Portrait | — | 3:4 ratio | Replace SVG in `.about-portrait` |
| Gallery 1 | Solstice | 180×240 cm | `imgSrc` in PAINTINGS[0] |
| Gallery 2 | The Weight of Light | 200×150 cm | `imgSrc` in PAINTINGS[1] |
| Gallery 3 | Meridian | 160×160 cm | `imgSrc` in PAINTINGS[2] |
| Gallery 4 | Before the Storm | 220×160 cm | `imgSrc` in PAINTINGS[3] |
| Gallery 5 | Vesper | 170×230 cm | `imgSrc` in PAINTINGS[4] |
| Gallery 6 | Expanse | 200×200 cm | `imgSrc` in PAINTINGS[5] |

### Things client needs to fill in
- Real bio text (3 paragraphs in EN — HE/DE will need translation)
- Phone number (currently `+1 (000) 000-0000`)
- OG image + canonical URL in `<head>`
- Formspree (or other) endpoint in the form's `TODO` comment
- GA4 tag ID in the commented-out gtag snippet

---

## QA Results (last run)

| Category | Status | Notes |
|---|---|---|
| Completeness | ✅ PASS | All sections present |
| Multi-language | ✅ PASS | EN/HE/DE complete, RTL works |
| Gallery | ✅ PASS | Shuffle, hover, lightbox, GA hooks |
| Lightbox | ✅ PASS | Fade, nav, counter, ESC/arrows |
| Responsiveness | ✅ PASS | About breakpoint fixed (768px) |
| Animations | ✅ PASS | IntersectionObserver, stagger, nav |
| Contact Form | ✅ PASS | All fields, success state, TODO comment |
| SEO | ✅ PASS | Title, meta, OG, canonical placeholders |
| Accessibility | ✅ PASS | Focus trap added to lightbox |
| Code Quality | ✅ PASS | Comments, CSS vars, slot markers |
| RTL Layout | ✅ PASS | Logical props + rtl overrides |

---

## Open Tasks

### Required (Reviewer fixes — ✅ DONE)
- [x] Fix About breakpoint: `max-width: 767px` → `max-width: 768px`
- [x] Add focus trap to lightbox (keyboard/a11y)

### Client deliverables needed
- [ ] Real painting images (8 slots: 1 hero, 1 portrait, 6 gallery)
- [ ] Final bio copy in EN (Architect used placeholder text)
- [ ] Phone number
- [ ] OG image
- [ ] Domain / canonical URL
- [ ] Formspree (or backend) endpoint
- [ ] GA4 tag ID

### Nice-to-have (optional)
- [ ] `prefers-reduced-motion` media query to disable animations
- [ ] Push to remote GitHub repo (local only so far)

---

## Git State

- Repo: local only — `main` branch, 2 commits
- Commit 1: workers + orchestrator
- Commit 2: `index.html` (Architect draft)
- Remote: https://github.com/Merom-accept/Eleanor_Website

---

## File Structure

```
Eleanor website/
├── index.html            ← THE website (current draft)
├── PROJECT_STATUS.md     ← this file
├── orchestrator.py       ← runs all 5 workers in sequence
├── chat_step.py          ← Planner conversation runner (used in chat)
├── requirements.txt      ← anthropic>=0.40.0
├── .env.example          ← copy to .env, add API key
├── .gitignore            ← ignores output/, .env
├── workers/
│   ├── base.py           ← streaming base class
│   ├── planner.py        ← interactive planner
│   ├── designer.py
│   ├── architect.py
│   ├── qa.py
│   └── reviewer.py
└── output/               ← gitignored working files
    └── index.html        ← working copy (same as root)
```
