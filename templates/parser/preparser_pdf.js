const regex = /^@import\s+"(.*\.pdf)"\s*(\{.*?\})?/mg;
markdown = markdown.replace(regex, (match, pdf, argument, offset) => {
    const replacement = `
<div style="display: flex; justify-content: center; flex-wrap: wrap;">

@import "${pdf}"${argument ? " " + argument : ""}

</div>

`;
    // The trailing \s* of the regex may swallow newlines after the directive,
    // so derive both shift deltas from the real newline counts: lines before
    // the preserved @import text, and lines after the whole replaced span.
    const origLine = globalThis.__mdcssOrigLine(markdown.slice(0, offset).split("\n").length);
    const d1 = (replacement.slice(0, replacement.indexOf("@import")).match(/\n/g) || []).length;
    const d2 = (replacement.match(/\n/g) || []).length - (match.match(/\n/g) || []).length - d1;
    globalThis.__mdcssRecordShift(origLine, d1);
    globalThis.__mdcssRecordShift(origLine + 1, d2);
    return replacement;
});