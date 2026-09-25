import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const MarkdownIt = require('markdown-it');

const input = JSON.parse(readFileSync(0, 'utf8'));
const preFn = new Function('markdown', `${input.pre}\nreturn markdown;`);
const postFn = new Function('html', `${input.post}\nreturn html;`);
const md = new MarkdownIt({ html: true });

process.stdout.write(JSON.stringify({ html: postFn(md.render(preFn(input.markdown))) }));
