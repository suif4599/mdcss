// Executes the assembled parser.js fragments for the pipeline tests.
// Python owns the fragment order (src.builder.build_parser_blocks) and sends
// the assembled pre/post code as JSON on stdin; this file only supplies the
// plumbing: pre(markdown) -> markdown, post(html) -> html, plus the
// line-shift ledger state that MPE keeps alive on globalThis between the
// two hooks. The html input is a fixture baked from a real markdown-it
// (html:true) capture — MPE's own crossnote renderer cannot be imported
// here; test_md/ is the manual crosscheck against the real preview.
import { readFileSync } from 'node:fs';

const input = JSON.parse(readFileSync(0, 'utf8'));

const preFn = new Function('markdown', `${input.pre}\nreturn markdown;`);
const postFn = new Function('html', `${input.post}\nreturn html;`);

const markdown = preFn(input.markdown ?? '');
const html = postFn(input.html ?? '');

const shifts = (globalThis.__MDCSS_LINE_SHIFTS__ || []).map((s) => [s.o, s.d]);
const mapped = [];
for (let i = 1; i <= Math.max(1, markdown.split('\n').length); i += 1) {
    mapped.push(globalThis.__mdcssOrigLine(i));
}
process.stdout.write(JSON.stringify({ markdown, html, shifts, mapped }));
