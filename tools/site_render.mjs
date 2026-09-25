import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const MarkdownIt = require('markdown-it');
const Prism = require('prismjs');
for (const lang of ['json', 'markdown', 'python', 'bash', 'yaml', 'toml', 'diff', 'sql', 'rust', 'go', 'java', 'c', 'cpp']) {
    require(`prismjs/components/prism-${lang}`);
}

const input = JSON.parse(readFileSync(0, 'utf8'));
const preFn = new Function('markdown', `${input.pre}\nreturn markdown;`);
const postFn = new Function('html', `${input.post}\nreturn html;`);

const md = new MarkdownIt({ html: true, linkify: true, langPrefix: 'language-' });

function escapeHtml(text) {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function escapeAttr(text) {
    return escapeHtml(text).replace(/'/g, '&#39;');
}

const PRISM_ALIASES = {
    html: 'markup', xml: 'markup', svg: 'markup', js: 'javascript', sh: 'bash',
    shell: 'bash', zsh: 'bash', yml: 'yaml', py: 'python', md: 'markdown',
};
function grammarFor(language) {
    return Prism.languages[PRISM_ALIASES[language] || language];
}

function parseFenceInfo(source) {
    let rest = source.trim();
    let language = '';
    let title = '';
    let lineNumbers = false;
    const options = /^\{([^{}]+)\}/.exec(rest);
    if (options) {
        const classes = [...options[1].matchAll(/\.([A-Za-z][\w-]*)/g)].map((m) => m[1]);
        language = (classes.find((c) => c.toLowerCase() !== 'line-numbers') || '').toLowerCase();
        lineNumbers = classes.some((c) => c.toLowerCase() === 'line-numbers');
        rest = rest.slice(options[0].length).trim();
    }
    if (!language) {
        const lang = /^([^\s{]+)/.exec(rest);
        if (lang) {
            language = lang[1].toLowerCase();
            rest = rest.slice(lang[0].length).trim();
        }
    }
    const titleMatch = /(?:^|\s)title=(?:"([^"]*)"|'([^']*)'|([^\s]+))/.exec(rest);
    if (titleMatch) title = titleMatch[1] ?? titleMatch[2] ?? titleMatch[3] ?? '';
    lineNumbers = lineNumbers || /(?:^|\s)(?:line-numbers|linenos)(?=\s|$)/.test(rest);
    return { language, title, lineNumbers };
}

md.renderer.rules.fence = (tokens, index) => {
    const token = tokens[index];
    const info = parseFenceInfo(token.info);
    const grammar = grammarFor(info.language);
    const body = grammar
        ? Prism.highlight(token.content, grammar, PRISM_ALIASES[info.language] || info.language)
        : escapeHtml(token.content);
    const title = info.title || info.language || 'text';
    const langLabel = info.title && info.language
        ? `<span class="code-lang">${escapeAttr(info.language)}</span>` : '';
    return [
        `<div class="code-block" data-lang="${escapeAttr(info.language)}"${info.lineNumbers ? ' data-line-numbers="true"' : ''}>`,
        `<div class="code-block-head"><span class="code-title">${escapeHtml(title)}</span>${langLabel}</div>`,
        `<pre><code class="language-${escapeAttr(info.language)}">${body}</code></pre>`,
        `</div>`,
    ].join('');
};

md.renderer.rules.table_open = () => '<div class="table-wrap"><table>';
md.renderer.rules.table_close = () => '</table></div>';

const defaultLink = md.renderer.rules.link_open;
md.renderer.rules.link_open = (tokens, index, options, env, self) => {
    const href = tokens[index].attrGet('href') ?? '';
    if (/^https?:/i.test(href)) {
        tokens[index].attrSet('target', '_blank');
        tokens[index].attrSet('rel', 'noopener noreferrer');
    }
    return defaultLink ? defaultLink(tokens, index, options, env, self) : self.renderToken(tokens, index, options);
};

const defaultImage = md.renderer.rules.image;
md.renderer.rules.image = (tokens, index, options, env, self) => {
    tokens[index].attrSet('loading', 'lazy');
    tokens[index].attrSet('decoding', 'async');
    return defaultImage ? defaultImage(tokens, index, options, env, self) : self.renderToken(tokens, index, options);
};

const CALLOUT_ALIASES = {
    summary: 'abstract', tldr: 'abstract', hint: 'tip', important: 'tip',
    check: 'success', done: 'success', help: 'question', faq: 'question',
    caution: 'warning', attention: 'warning', fail: 'failure', missing: 'failure',
    error: 'danger', bug: 'danger', cite: 'quote',
};
const CALLOUT_TITLES = {
    note: '注', abstract: '摘要', info: '信息', todo: '待办', tip: '提示',
    success: '成功', question: '问题', warning: '警告', failure: '失败',
    danger: '危险', example: '示例', quote: '引用',
};
function normalizeCalloutType(value) {
    const type = value.toLowerCase();
    return (CALLOUT_ALIASES[type] ?? type.replace(/[^a-z0-9_-]/g, '')) || 'note';
}
function matchingClose(tokens, start, openType, closeType) {
    let depth = 0;
    for (let index = start; index < tokens.length; index++) {
        if (tokens[index].type === openType) depth++;
        else if (tokens[index].type === closeType && --depth === 0) return index;
    }
    return -1;
}

md.core.ruler.push('obsidian_callouts', (state) => {
    for (let index = 0; index < state.tokens.length; index++) {
        const open = state.tokens[index];
        if (open.type !== 'blockquote_open') continue;
        const paragraphOpen = state.tokens[index + 1];
        const inline = state.tokens[index + 2];
        if (paragraphOpen?.type !== 'paragraph_open' || inline?.type !== 'inline') continue;
        const firstBreak = inline.content.indexOf('\n');
        const firstLine = firstBreak >= 0 ? inline.content.slice(0, firstBreak) : inline.content;
        const marker = /^\[!([A-Za-z][A-Za-z0-9_-]{0,31})\]([+-])?(?:[ \t]+(.+?))?[ \t]*$/.exec(firstLine);
        if (!marker) continue;
        const closeIndex = matchingClose(state.tokens, index, 'blockquote_open', 'blockquote_close');
        if (closeIndex < 0) continue;
        const type = normalizeCalloutType(marker[1]);
        const fold = marker[2] ?? '';
        const title = marker[3]?.trim() || CALLOUT_TITLES[type] || type;
        open.type = 'callout_open';
        open.tag = fold ? 'details' : 'aside';
        open.meta = { type, title, fold };
        const close = state.tokens[closeIndex];
        close.type = 'callout_close';
        close.tag = open.tag;
        close.meta = { fold };
        const remaining = firstBreak >= 0 ? inline.content.slice(firstBreak + 1) : '';
        if (remaining.trim()) {
            const children = [];
            md.inline.parse(remaining, state.md, state.env, children);
            inline.content = remaining;
            inline.children = children;
        } else {
            const paragraphClose = state.tokens[index + 3];
            if (paragraphClose?.type === 'paragraph_close') state.tokens.splice(index + 1, 3);
        }
    }
    return true;
});
md.renderer.rules.callout_open = (tokens, index) => {
    const { type, title, fold } = tokens[index].meta;
    if (fold) {
        return `<details class="callout callout-${escapeAttr(type)}" data-callout="${escapeAttr(type)}"${fold === '+' ? ' open' : ''}><summary class="callout-title">${escapeHtml(title)}</summary><div class="callout-content">`;
    }
    return `<aside class="callout callout-${escapeAttr(type)}" data-callout="${escapeAttr(type)}"><div class="callout-title">${escapeHtml(title)}</div><div class="callout-content">`;
};
md.renderer.rules.callout_close = (tokens, index) => `</div>${tokens[index].meta.fold ? '</details>' : '</aside>'}`;

const headings = [];
const slugCounts = new Map();
function slugify(text) {
    const base = text.toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu, '').trim().replace(/\s+/g, '-') || 'section';
    const n = (slugCounts.get(base) ?? 0) + 1;
    slugCounts.set(base, n);
    return n === 1 ? base : `${base}-${n}`;
}
md.core.ruler.push('heading_ids', (state) => {
    for (let index = 0; index < state.tokens.length; index++) {
        const open = state.tokens[index];
        if (open.type !== 'heading_open') continue;
        const inline = state.tokens[index + 1];
        const text = ((inline?.children ?? []).filter((c) => c.type === 'text' || c.type === 'code_inline').map((c) => c.content).join('') || inline?.content || '').trim();
        const id = slugify(text);
        open.attrSet('id', id);
        headings.push({ level: Number(open.tag.slice(1)), text, id });
    }
    return true;
});

process.stdout.write(JSON.stringify({ html: postFn(md.render(preFn(input.markdown))), headings }));
