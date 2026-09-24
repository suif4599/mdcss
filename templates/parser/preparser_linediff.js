// Final line-accounting pass: record the whole pre pipeline's line shifts
// by diffing the snapshotted original (taken by preparser_lineshift.js)
// against the final transformed markdown. preparser_lineshift.js owns the
// diff machinery and the ledger; this must stay the last pre pass so the
// diff sees exactly the text markdown-it will render.
globalThis.__mdcssRecordLineDiff(globalThis.__MDCSS_ORIGINAL_MARKDOWN__, markdown);
