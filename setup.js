/**
 * One-time admin setup.
 * Sets the admin password (stored as a bcrypt hash — never plaintext)
 * and generates a random session secret.
 *
 * Run:  npm run setup
 */

const bcrypt   = require('bcrypt');
const readline = require('readline');
const crypto   = require('crypto');
const fs       = require('fs');

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const ask = q => new Promise(resolve => rl.question(q, resolve));

async function main() {
  console.log('\n  Eleanor Admin Setup\n  ─────────────────────────────────────');

  const pw1 = await ask('  New admin password (min 8 chars): ');
  if (pw1.length < 8) {
    console.log('\n  ✗  Password must be at least 8 characters.\n');
    rl.close(); return;
  }

  const pw2 = await ask('  Confirm password: ');
  if (pw1 !== pw2) {
    console.log('\n  ✗  Passwords do not match.\n');
    rl.close(); return;
  }

  console.log('\n  Hashing… (this takes a moment)');
  const hash   = await bcrypt.hash(pw1, 12);
  const secret = crypto.randomBytes(32).toString('hex');

  /* Read existing .env, strip lines we're replacing */
  const envPath = '.env';
  let existing  = '';
  if (fs.existsSync(envPath)) {
    existing = fs.readFileSync(envPath, 'utf8')
      .split('\n')
      .filter(l => !l.startsWith('ADMIN_PASSWORD_HASH=') && !l.startsWith('SESSION_SECRET='))
      .join('\n')
      .trim();
  }

  const content = (existing ? existing + '\n' : '')
    + `ADMIN_PASSWORD_HASH=${hash}\n`
    + `SESSION_SECRET=${secret}\n`;

  fs.writeFileSync(envPath, content);

  /* Create required directories */
  ['uploads', 'data'].forEach(dir => {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir);
  });

  console.log('\n  ✓  .env updated  (bcrypt hash only — no plaintext password stored)');
  console.log('  ✓  uploads/ and data/ directories ready');
  console.log('\n  Start the server:  npm start');
  console.log('  Admin panel:       http://localhost:3000/admin\n');

  rl.close();
}

main().catch(err => { console.error(err); process.exit(1); });
