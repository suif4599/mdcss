__mdcssHasIndent = false;
if (markdown.trimStart().startsWith('@indent')) {
    markdown = markdown.trimStart().slice('@indent'.length);
    __mdcssHasIndent = true;
} else if (markdown.trimStart().startsWith('<indent>')) {
    markdown = markdown.trimStart().slice('<indent>'.length);
    __mdcssHasIndent = true;
}
if (__mdcssHasIndent) {
    // the leading "<div>\n\n" pushes every content line down by 2 lines
    globalThis.__mdcssRecordShift(1, 2);
    markdown = `<div class="has-indent">

${markdown}

</div>

`;
}
