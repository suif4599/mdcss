// Paragraph-indent document flag: @indent / <indent> (after leading
// whitespace) wraps the whole document. No line-shift bookkeeping needed
// here — preparser_linediff.js diffs the pipeline's final text.
const __mdcssHead = markdown.trimStart();
if (__mdcssHead.startsWith("@indent") || __mdcssHead.startsWith("<indent>")) {
    const __mdcssFlag = __mdcssHead.startsWith("@indent") ? "@indent" : "<indent>";
    markdown = `<div class="has-indent">

${__mdcssHead.slice(__mdcssFlag.length)}

</div>

`;
}
