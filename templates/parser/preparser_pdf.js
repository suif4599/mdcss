// Centers @import-ed PDFs by wrapping the directive in a flex div; the
// directive itself is preserved verbatim for crossnote's import handling.
// Line-shift bookkeeping lives in preparser_linediff.js.
markdown = markdown.replace(
    /^@import\s+"(.*\.pdf)"\s*(\{.*?\})?/mg,
    (match, pdf, argument) => `
<div style="display: flex; justify-content: center; flex-wrap: wrap;">

@import "${pdf}"${argument ? " " + argument : ""}

</div>

`
);
