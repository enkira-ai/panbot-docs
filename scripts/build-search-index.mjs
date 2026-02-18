/**
 * Build-time search index generator for Lunr.js
 *
 * Reads all markdown/mdx files in src/content/docs/, strips frontmatter
 * and markdown syntax, builds a Lunr.js index, and writes:
 *   - public/search-index.json  (serialised Lunr index)
 *   - public/search-docs.json   (document metadata for result display)
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import lunr from 'lunr';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DOCS_DIR = path.resolve(__dirname, '../src/content/docs');
const PUBLIC_DIR = path.resolve(__dirname, '../public');

/** Derive a category label from the directory name */
function getCategory(relPath) {
  const parts = relPath.split(path.sep);
  if (parts.length > 1) {
    return parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
  }
  return 'General';
}

/** Derive the URL slug from a relative file path */
function toSlug(relPath) {
  return relPath
    .replace(/\.mdx?$/, '/')
    .replace(/index\/$/, '')
    .split(path.sep)
    .join('/');
}

/** Strip YAML frontmatter from markdown content */
function stripFrontmatter(content) {
  return content.replace(/^---[\s\S]*?---\n*/, '');
}

/** Strip markdown syntax for cleaner index content */
function stripMarkdown(text) {
  return text
    .replace(/```[\s\S]*?```/g, '')        // fenced code blocks
    .replace(/`[^`]+`/g, '')               // inline code
    .replace(/!\[.*?\]\(.*?\)/g, '')        // images
    .replace(/\[([^\]]+)\]\(.*?\)/g, '$1')  // links → text
    .replace(/#{1,6}\s+/g, '')              // headings
    .replace(/[*_~]{1,3}/g, '')             // bold/italic/strikethrough
    .replace(/>\s+/gm, '')                  // blockquotes
    .replace(/[-*+]\s+/gm, '')             // list markers
    .replace(/\d+\.\s+/gm, '')             // numbered lists
    .replace(/\|[^|\n]+/g, '')             // table cells
    .replace(/<[^>]+>/g, '')                // HTML tags
    .replace(/import\s+.*?;?\n/g, '')      // ESM imports (mdx)
    .replace(/\n{3,}/g, '\n\n')            // collapse blank lines
    .trim();
}

/** Extract the title from frontmatter or first heading */
function extractTitle(raw) {
  const fmMatch = raw.match(/^---[\s\S]*?title:\s*['"]?(.+?)['"]?\s*$/m);
  if (fmMatch) return fmMatch[1];
  const headingMatch = raw.match(/^#\s+(.+)$/m);
  if (headingMatch) return headingMatch[1];
  return 'Untitled';
}

/** Recursively collect all .md/.mdx files */
function collectFiles(dir, base = dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...collectFiles(full, base));
    } else if (/\.mdx?$/.test(entry.name)) {
      files.push(path.relative(base, full));
    }
  }
  return files;
}

// --- Main ---

const relPaths = collectFiles(DOCS_DIR);
const docs = [];

for (const relPath of relPaths) {
  const raw = fs.readFileSync(path.join(DOCS_DIR, relPath), 'utf-8');
  const title = extractTitle(raw);
  const body = stripMarkdown(stripFrontmatter(raw));
  const category = getCategory(relPath);
  const slug = toSlug(relPath);

  docs.push({ slug, title, body, category });
}

// Build Lunr index
const idx = lunr(function () {
  this.ref('slug');
  this.field('title', { boost: 10 });
  this.field('body');
  this.field('category', { boost: 5 });

  for (const doc of docs) {
    this.add(doc);
  }
});

// Write outputs
fs.mkdirSync(PUBLIC_DIR, { recursive: true });

fs.writeFileSync(
  path.join(PUBLIC_DIR, 'search-index.json'),
  JSON.stringify(idx),
);

// Store doc metadata (title, category, snippet) for rendering results
const docsMeta = docs.map((d) => ({
  slug: d.slug,
  title: d.title,
  category: d.category,
  // First 200 chars as default snippet
  snippet: d.body.slice(0, 200).replace(/\n+/g, ' '),
}));

fs.writeFileSync(
  path.join(PUBLIC_DIR, 'search-docs.json'),
  JSON.stringify(docsMeta),
);

console.log(`[search] Indexed ${docs.length} documents → public/search-index.json`);
