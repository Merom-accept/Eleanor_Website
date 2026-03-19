require('dotenv').config();

const express  = require('express');
const session  = require('express-session');
const bcrypt   = require('bcrypt');
const multer   = require('multer');
const Database = require('better-sqlite3');
const path     = require('path');
const fs       = require('fs');
const crypto   = require('crypto');

/* ── GeoIP (optional — degrades gracefully if not installed) ─── */
let geoip = null;
try { geoip = require('geoip-lite'); } catch { /* country tracking disabled */ }

const app  = express();
const PORT = process.env.PORT || 3000;

/* ── Directories ─────────────────────────────────────────────── */
['uploads', 'data'].forEach(dir => {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir);
});

/* ── Database ────────────────────────────────────────────────── */
const db = new Database(path.join('data', 'submissions.db'));
db.exec(`
  CREATE TABLE IF NOT EXISTS page_visits (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_hash TEXT    NOT NULL,
    is_new       INTEGER NOT NULL DEFAULT 0,
    country      TEXT    NOT NULL DEFAULT 'XX',
    visited_at   DATETIME DEFAULT CURRENT_TIMESTAMP
  )
`);

db.exec(`
  CREATE TABLE IF NOT EXISTS submissions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL,
    phone      TEXT,
    interest   TEXT,
    message    TEXT NOT NULL
  )
`);

/* ── Image slots ─────────────────────────────────────────────── */
const SLOTS     = ['hero','portrait','gallery-1','gallery-2','gallery-3','gallery-4','gallery-5','gallery-6'];
const IMG_EXTS  = ['.jpg','.jpeg','.png','.webp'];

function findSlotFile(slot) {
  for (const ext of IMG_EXTS) {
    const p = path.join('uploads', slot + ext);
    if (fs.existsSync(p)) return p;
  }
  return null;
}

function deleteSlotFiles(slot) {
  IMG_EXTS.forEach(ext => {
    const p = path.join('uploads', slot + ext);
    if (fs.existsSync(p)) fs.unlinkSync(p);
  });
}

/* ── Cookie helper (no cookie-parser dep needed) ─────────────── */
function parseCookies(req) {
  const out = {};
  (req.headers.cookie || '').split(';').forEach(c => {
    const [k, ...v] = c.split('=');
    if (k?.trim()) out[k.trim()] = decodeURIComponent(v.join('=').trim());
  });
  return out;
}

/* ── Visit tracking middleware ───────────────────────────────── */
const VISIT_COOKIE    = 'eleanor_vid';
const VISIT_COOKIE_MS = 365 * 24 * 60 * 60 * 1000;
const insertVisit     = db.prepare('INSERT INTO page_visits (visitor_hash, is_new, country) VALUES (?, ?, ?)');

app.use((req, res, next) => {
  if (req.method === 'GET' && (req.path === '/' || req.path === '/index.html')) {
    try {
      const cookies = parseCookies(req);
      let token     = cookies[VISIT_COOKIE];
      const isNew   = token ? 0 : 1;

      if (!token) {
        token = crypto.randomBytes(32).toString('hex');
        res.cookie(VISIT_COOKIE, token, {
          maxAge: VISIT_COOKIE_MS, httpOnly: true, sameSite: 'lax', path: '/'
        });
      }

      const visitorHash = crypto.createHash('sha256').update(token).digest('hex');
      const rawIp  = (req.headers['x-forwarded-for'] || '').split(',')[0].trim()
                     || req.socket?.remoteAddress || '';
      let country  = 'XX';
      if (geoip && rawIp) {
        const geo = geoip.lookup(rawIp);
        if (geo?.country) country = geo.country;
      }

      insertVisit.run(visitorHash, isNew, country);
    } catch (err) {
      console.error('[visit-tracker]', err.message);
    }
  }
  next();
});

/* ── Multer (memory → manual write so we can clean old ext) ──── */
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 20 * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    cb(null, IMG_EXTS.includes(ext));
  }
});

/* ── Session ─────────────────────────────────────────────────── */
app.use(session({
  secret:            process.env.SESSION_SECRET || 'change-me-run-setup',
  resave:            false,
  saveUninitialized: false,
  cookie: { httpOnly: true, sameSite: 'lax', maxAge: 24 * 60 * 60 * 1000 }
}));

/* ── Body parsers + static ───────────────────────────────────── */
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(express.static(path.join(__dirname)));
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

/* ── Auth middleware ─────────────────────────────────────────── */
function requireAuth(req, res, next) {
  if (req.session.authenticated) return next();
  res.redirect('/login');
}

/* ═══════════════════════════════════════════════════════════════
   PUBLIC ROUTES
═══════════════════════════════════════════════════════════════ */

/* Image manifest — tells the frontend which slots have real images */
app.get('/api/images', (_req, res) => {
  const manifest = {};
  SLOTS.forEach(slot => {
    const file = findSlotFile(slot);
    if (file) manifest[slot] = '/uploads/' + path.basename(file);
  });
  res.json(manifest);
});

/* Contact form submission */
app.post('/api/contact', (req, res) => {
  const { name, email, phone, interest, message } = req.body;
  if (!name || !email || !message) {
    return res.status(400).json({ error: 'name, email and message are required' });
  }
  db.prepare(`
    INSERT INTO submissions (name, email, phone, interest, message)
    VALUES (?, ?, ?, ?, ?)
  `).run(name.trim(), email.trim(), (phone||'').trim(), (interest||'').trim(), message.trim());
  res.json({ ok: true });
});

/* ═══════════════════════════════════════════════════════════════
   AUTH ROUTES
═══════════════════════════════════════════════════════════════ */

app.get('/login', (_req, res) => {
  res.sendFile(path.join(__dirname, 'login.html'));
});

app.post('/api/login', async (req, res) => {
  const hash = process.env.ADMIN_PASSWORD_HASH;
  if (!hash) {
    return res.status(500).json({ error: 'Admin not configured. Run: npm run setup' });
  }
  const ok = await bcrypt.compare(req.body.password || '', hash);
  if (ok) {
    req.session.authenticated = true;
    res.json({ ok: true });
  } else {
    res.status(401).json({ error: 'Incorrect password' });
  }
});

app.post('/api/logout', (req, res) => {
  req.session.destroy(() => res.json({ ok: true }));
});

/* ═══════════════════════════════════════════════════════════════
   ADMIN — all routes require auth
═══════════════════════════════════════════════════════════════ */

app.get('/admin', requireAuth, (_req, res) => {
  res.sendFile(path.join(__dirname, 'admin.html'));
});

/* List submissions */
app.get('/api/admin/submissions', requireAuth, (_req, res) => {
  const rows = db.prepare('SELECT * FROM submissions ORDER BY created_at DESC').all();
  res.json(rows);
});

/* Delete a submission */
app.delete('/api/admin/submissions/:id', requireAuth, (req, res) => {
  const info = db.prepare('DELETE FROM submissions WHERE id = ?').run(req.params.id);
  res.json({ ok: info.changes > 0 });
});

/* Upload image to a slot */
app.post('/api/admin/upload/:slot', requireAuth, (req, res, next) => {
  if (!SLOTS.includes(req.params.slot)) {
    return res.status(400).json({ error: 'Unknown slot' });
  }
  next();
}, upload.single('image'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No valid image file received' });

  const ext      = path.extname(req.file.originalname).toLowerCase();
  const filename = req.params.slot + ext;

  deleteSlotFiles(req.params.slot);                           // remove old extensions
  fs.writeFileSync(path.join('uploads', filename), req.file.buffer);

  res.json({ ok: true, url: '/uploads/' + filename });
});

/* Analytics summary */
app.get('/api/admin/analytics', requireAuth, (_req, res) => {
  const total     = db.prepare('SELECT COUNT(*) as n FROM page_visits').get().n;
  const unique    = db.prepare('SELECT COUNT(DISTINCT visitor_hash) as n FROM page_visits').get().n;
  const returning = db.prepare('SELECT COUNT(DISTINCT visitor_hash) as n FROM page_visits WHERE is_new = 0').get().n;
  const today     = db.prepare("SELECT COUNT(*) as n FROM page_visits WHERE date(visited_at) = date('now')").get().n;

  // Last 7 days — one row per day, fill missing days with 0 in JS
  const rows7 = db.prepare(`
    SELECT date(visited_at) as d, COUNT(*) as n
    FROM page_visits
    WHERE date(visited_at) >= date('now', '-6 days')
    GROUP BY d ORDER BY d
  `).all();

  const last7 = [];
  for (let i = 6; i >= 0; i--) {
    const d  = new Date();
    d.setUTCDate(d.getUTCDate() - i);
    const ds = d.toISOString().slice(0, 10);
    last7.push({ date: ds, count: rows7.find(r => r.d === ds)?.n || 0 });
  }

  const topCountries = db.prepare(`
    SELECT country, COUNT(*) as visits, COUNT(DISTINCT visitor_hash) as unique_visitors
    FROM page_visits
    GROUP BY country ORDER BY visits DESC LIMIT 5
  `).all();

  res.json({ total, unique, returning, today, last7, topCountries });
});

/* Remove image from a slot */
app.delete('/api/admin/image/:slot', requireAuth, (req, res) => {
  if (!SLOTS.includes(req.params.slot)) {
    return res.status(400).json({ error: 'Unknown slot' });
  }
  const existed = !!findSlotFile(req.params.slot);
  deleteSlotFiles(req.params.slot);
  res.json({ ok: existed });
});

/* ── Start ───────────────────────────────────────────────────── */
app.listen(PORT, () => {
  console.log(`\n  Eleanor website  →  http://localhost:${PORT}`);
  console.log(`  Admin panel      →  http://localhost:${PORT}/admin\n`);
});
