const __MDCSS_FENCE_TOKEN_PREFIX__ = "@@MDCSS_FENCE_BLOCK_";
globalThis.__MDCSS_FENCED_BLOCKS__ = [];

// Line-based fence scanner (CommonMark fenced code blocks): 0-3 spaces of
// indentation, backtick and tilde fences, unclosed fences run to EOF. The
// old single regex only saw column-0 backtick fences, so mdcss-syntax text
// inside indented fences (e.g. in list items), tilde fences or unclosed
// fences leaked into the rewriters and got corrupted. Extracted blocks
// collapse to a one-line token here and are restored by
// preparser_fence_restore.js before markdown-it, so the net line count the
// renderer sees is unchanged.
function __mdcssExtractFences(markdown) {
    const lines = markdown.split("\n");
    const out = [];
    const openRe = /^ {0,3}(`{3,}|~{3,})(.*)$/;
    let i = 0;
    while (i < lines.length) {
        const open = lines[i].match(openRe);
        if (!open || (open[1][0] === "`" && open[2].indexOf("`") !== -1)) {
            out.push(lines[i]);
            i += 1;
            continue;
        }
        const marker = open[1][0];
        const closeRe = new RegExp("^ {0,3}" + marker + "{" + open[1].length + ",}[ \t]*$");
        let j = i + 1;
        while (j < lines.length && !closeRe.test(lines[j])) {
            j += 1;
        }
        const blockEnd = Math.min(j + 1, lines.length);
        const block = lines.slice(i, blockEnd).join("\n");
        const index = globalThis.__MDCSS_FENCED_BLOCKS__.push(block) - 1;
        out.push(__MDCSS_FENCE_TOKEN_PREFIX__ + index + "@@");
        i = blockEnd;
    }
    return out.join("\n");
}
markdown = __mdcssExtractFences(markdown);
