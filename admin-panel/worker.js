/**
 * Captain Guido Admin Worker
 * Deploy to Cloudflare Workers (free tier)
 *
 * Environment variables to set in Cloudflare dashboard:
 *   ADMIN_PASSWORD  — shared password for Glenn + Jude
 *   GITHUB_TOKEN    — fine-grained PAT with Contents read+write
 *   GITHUB_REPO     — glenngallacher1-lab/captain-guido
 */

const SCRIPT_PATH = 'script.js';

// ── GitHub helpers ─────────────────────────────────────────────────────────────
async function ghGet(env) {
  const url = `https://api.github.com/repos/${env.GITHUB_REPO}/contents/${SCRIPT_PATH}`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'User-Agent': 'cgc-admin-bot',
    },
  });
  if (!res.ok) throw new Error(`GitHub GET failed: ${res.status}`);
  const data = await res.json();
  const content = atob(data.content.replace(/\n/g, ''));
  return { content, sha: data.sha };
}

async function ghPut(env, content, sha, message) {
  const url = `https://api.github.com/repos/${env.GITHUB_REPO}/contents/${SCRIPT_PATH}`;
  const encoded = btoa(unescape(encodeURIComponent(content)));
  const res = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'Content-Type': 'application/json',
      'User-Agent': 'cgc-admin-bot',
    },
    body: JSON.stringify({ message, content: encoded, sha }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`GitHub PUT failed: ${res.status} — ${err}`);
  }
}

// ── Parsers / mutators ─────────────────────────────────────────────────────────
function parseImpact(content) {
  const out = {};
  const fields = {
    launched:          /launched:\s*(true|false)/,
    chaptersUnlocked:  /chaptersUnlocked:\s*(\d+)/,
    lbsRemoved:        /lbsRemoved:\s*(\d+)/,
    milesCleaned:      /milesCleaned:\s*(\d+)/,
    donationsVerified: /donationsVerified:\s*(\d+)/,
    donationUSD:       /donationUSD:\s*(\d+)/,
  };
  for (const [key, rx] of Object.entries(fields)) {
    const m = content.match(rx);
    if (m) out[key] = key === 'launched' ? m[1] === 'true' : parseInt(m[1], 10);
  }
  return out;
}

function getChapterStatus(content) {
  const matches = [...content.matchAll(/\{ name: "([^"]+)"[\s\S]*?unlocked: (true|false)/g)];
  return matches.map(m => ({ name: m[1], unlocked: m[2] === 'true' }));
}

function setField(content, field, value) {
  if (typeof value === 'boolean') {
    return content.replace(
      new RegExp(`(${field}:\\s*)(?:true|false)`),
      `$1${value}`
    );
  }
  return content.replace(
    new RegExp(`(${field}:\\s*)\\d+`),
    `$1${value}`
  );
}

function unlockChapter(content, num) {
  // Split on chapter object openings, flip the nth one
  const parts = content.split(/(\{ name: ")/);
  let occurrence = 0;
  return parts.map((part, i) => {
    if (i % 2 === 1) return part; // separator token
    if (i > 0) {
      occurrence++;
      if (occurrence === num) {
        return part.replace(/unlocked:\s*false/, 'unlocked: true');
      }
    }
    return part;
  }).join('');
}

function addMilestone(content, date, title, location, impact) {
  const entry = `\n      { date: '${date}', title: '${title}', location: '${location}', impact: '${impact}' }`;
  return content.replace(
    /(milestones:\s*\[)([\s\S]*?)(\s*\])/,
    (_, open, body, close) => {
      const trimmed = body.trimEnd();
      const sep = trimmed.length > 0 ? ',' : '';
      return `${open}${trimmed}${sep}${entry}\n    ${close.trimStart()}`;
    }
  );
}

// ── CORS headers ───────────────────────────────────────────────────────────────
function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin': origin || '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

// ── Main handler ───────────────────────────────────────────────────────────────
export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '*';

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
        status: 400, headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
      });
    }

    // Auth check
    if (body.password !== env.ADMIN_PASSWORD) {
      return new Response(JSON.stringify({ error: 'Incorrect password' }), {
        status: 401, headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
      });
    }

    const respond = (data, status = 200) =>
      new Response(JSON.stringify(data), {
        status,
        headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
      });

    try {
      const { action } = body;

      // ── status ──────────────────────────────────────────────────────────────
      if (action === 'status') {
        const { content } = await ghGet(env);
        return respond({
          impact: parseImpact(content),
          chapters: getChapterStatus(content),
        });
      }

      // ── unlock_chapter ───────────────────────────────────────────────────────
      if (action === 'unlock_chapter') {
        const num = parseInt(body.chapter, 10);
        if (!num || num < 1 || num > 12)
          return respond({ error: 'chapter must be 1–12' }, 400);

        const { content, sha } = await ghGet(env);
        const chapters = getChapterStatus(content);
        if (chapters[num - 1]?.unlocked)
          return respond({ error: `Chapter ${num} is already unlocked` }, 400);

        let updated = unlockChapter(content, num);
        const current = parseImpact(updated).chaptersUnlocked || 0;
        updated = setField(updated, 'chaptersUnlocked', current + 1);
        await ghPut(env, updated, sha, `🔓 Unlock Chapter ${num}: ${chapters[num-1]?.name} [admin panel]`);
        return respond({ ok: true, chaptersUnlocked: current + 1 });
      }

      // ── update_stats ─────────────────────────────────────────────────────────
      if (action === 'update_stats') {
        const { content, sha } = await ghGet(env);
        let updated = content;
        const allowed = ['lbsRemoved','milesCleaned','donationsVerified','donationUSD','chaptersUnlocked'];
        for (const field of allowed) {
          if (body[field] !== undefined) {
            updated = setField(updated, field, parseInt(body[field], 10));
          }
        }
        await ghPut(env, updated, sha, '📊 Update impact stats [admin panel]');
        return respond({ ok: true, impact: parseImpact(updated) });
      }

      // ── add_milestone ────────────────────────────────────────────────────────
      if (action === 'add_milestone') {
        const { date, title, location, impact } = body;
        if (!date || !title || !location || !impact)
          return respond({ error: 'date, title, location, impact are all required' }, 400);
        const { content, sha } = await ghGet(env);
        const updated = addMilestone(content, date, title, location, impact);
        await ghPut(env, updated, sha, `🏆 Add milestone: ${title} [admin panel]`);
        return respond({ ok: true });
      }

      // ── launch ───────────────────────────────────────────────────────────────
      if (action === 'launch') {
        const { content, sha } = await ghGet(env);
        const updated = setField(content, 'launched', true);
        await ghPut(env, updated, sha, '🚀 LAUNCH — flip site to live mode [admin panel]');
        return respond({ ok: true });
      }

      return respond({ error: `Unknown action: ${action}` }, 400);

    } catch (err) {
      return respond({ error: err.message }, 500);
    }
  },
};
