# Eleanor — Artist Portfolio Website

Portfolio website for Eleanor, a hyper-realistic large-scale oil painter. Three languages (EN / HE / DE), admin panel for image and submission management, deployed on Railway.

---

## Stack

- **Frontend** — Single-file HTML/CSS/JS (`index.html`). No frameworks, no build step.
- **Backend** — Node.js + Express (`server.js`)
- **Database** — SQLite via `better-sqlite3` (contact form submissions)
- **Auth** — bcrypt-hashed password + express-session (never stored in plaintext)
- **Hosting** — Railway (auto-deploys on push to `main`)

---

## Getting Started

### 1. Install dependencies
```bash
npm install
```

### 2. Set admin password (first time only)
```bash
npm run setup
```
Prompts for a password, writes a bcrypt hash to `.env`. No plaintext stored.

### 3. Start the server
```bash
npm start
```

- Site → http://localhost:3000
- Admin → http://localhost:3000/admin

---

## Admin Panel

`/admin` is session-protected. Features:

- **Image management** — upload/replace/remove images for 8 slots (hero background, artist portrait, 6 gallery paintings)
- **Contact submissions** — view and delete form submissions stored in SQLite

---

## Deployment (Railway)

Auto-deploys from the `main` branch. Set these environment variables in the Railway dashboard:

| Variable | How to get it |
|---|---|
| `ADMIN_PASSWORD_HASH` | Copy from your local `.env` after running `npm run setup` |
| `SESSION_SECRET` | Copy from your local `.env` after running `npm run setup` |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in values. Never commit `.env`.

```
ADMIN_PASSWORD_HASH=   # bcrypt hash — set via npm run setup
SESSION_SECRET=        # random hex string — set via npm run setup
```

---

## Things Still Needed (client content)

- [ ] Real painting images — upload via `/admin`
- [ ] Artist bio (EN) — edit `index.html`, search for placeholder bio text
- [ ] Phone number — search `+1 (000) 000-0000` in `index.html`
- [ ] OG image + canonical URL — in `<head>` of `index.html`
- [ ] GA4 tag ID — commented-out snippet in `<head>`
- [ ] Custom domain (optional)

---

## Project Structure

```
├── index.html          ← The website
├── server.js           ← Express server
├── setup.js            ← One-time password setup
├── admin.html          ← Admin panel
├── login.html          ← Admin login page
├── package.json
├── railway.json        ← Railway deployment config
├── workers/            ← AI pipeline (Planner→Designer→Architect→QA→Reviewer)
├── uploads/            ← Uploaded images (gitignored)
└── data/               ← SQLite database (gitignored)
```
