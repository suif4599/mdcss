// Block-level gap: a standalone, column-0 \\ or \\[size] line becomes a
// spacer div. This borrows LaTeX's line-break marker but stays block-level.
// Fenced code has already been tokenised by this point; indented code and
// indented (list) lines stay literal because only column 0 matches. Table
// cells and lines ending in \\ are untouched, so the table \\ literal and
// LaTeX formulas keep working. Front matter is kept verbatim (crossnote
// extracts it after this hook), so a literal \\ line inside YAML metadata is
// never rewritten. Four backslashes are the escape: Markdown renders two.
const __mdcssGapFrontMatter = /^---\r?\n[\s\S]*?\r?\n---[ \t]*\r?\n?/.exec(markdown);
const __mdcssGapHead = __mdcssGapFrontMatter ? __mdcssGapFrontMatter[0] : "";
const __mdcssGapBody = __mdcssGapHead ? markdown.slice(__mdcssGapHead.length) : markdown;

function __mdcssGapSize(raw) {
    const spec = (raw || "").trim();
    if (!spec) {
        return "1lh";
    }
    const match = /^(\d+(?:\.\d+)?)(lh|em|rem|px|pt)?$/i.exec(spec);
    if (!match) {
        return null;
    }
    const value = Number(match[1]);
    if (!Number.isFinite(value) || value <= 0) {
        return null;
    }
    const unit = (match[2] || "lh").toLowerCase();
    // Unitless values count blank lines; keep the default small. Explicit
    // lengths are trusted (cover pages etc.) but still capped against typos.
    if (!match[2] && value > 20) {
        return null;
    }
    if (match[2] && value > 1000) {
        return null;
    }
    return `${value}${unit}`;
}

markdown = __mdcssGapHead + __mdcssGapBody.replace(
    /^\\\\(?:\[([^\]\r\n]*)\])?[ \t]*\r?$/gm,
    (match, raw) => {
        const size = __mdcssGapSize(raw);
        if (size === null) {
            return match;
        }
        return `\n<div class="mdcss-gap" data-mdcss-gap="${size}" aria-hidden="true"></div>\n`;
    }
);
