// Caption content is moved into inline <span> markers before markdown-it
// runs, so it is rendered with the document (inline math in particular).
// The post pass consumes a marker into the figure's figcaption; a marker
// that never meets its figure stays inert text.
const MDCSS_CAPTION_CONTROL_RE = /^(\d{1,4})(%|px)?(Lf|Rf|r|L|R)?(i|I|m|M)?(?:\((\d{1,3}),(\d{1,3})\))?$/;
const MDCSS_CAPTION_IMG_RE = /!\[((?:\\.|[^\]\\\n])*)\]\(((?:\\.|[^()\\\n]|\([^()\n]*\))*)\)/g;

function mdcssCaptionOfAlt(alt) {
    const parts = alt.split("|");
    if (parts.length < 2) return null;
    const control = parts[0].trim();
    if (control !== "") {
        const match = control.match(MDCSS_CAPTION_CONTROL_RE);
        if (!match || Number(match[1]) <= 0) return null;
    }
    const caption = (parts[1] || "").trim();
    return caption || null;
}

// Applies rewrite to the line's prose segments, skipping inline code spans.
function mdcssMapProse(line, rewrite) {
    let out = "";
    let index = 0;
    while (index < line.length) {
        let next = line.indexOf("`", index);
        if (next < 0) next = line.length;
        if (next > index) {
            out += rewrite(line.slice(index, next));
            index = next;
            continue;
        }
        let end = index;
        while (line[end] === "`") end += 1;
        const ticks = line.slice(index, end);
        const close = line.indexOf(ticks, end);
        if (close < 0) {
            out += line.slice(index);
            break;
        }
        out += line.slice(index, close + ticks.length);
        index = close + ticks.length;
    }
    return out;
}

markdown = markdown.replace(
    /^([ \t]{0,3}Table(?:@(?:auto|zebra|nozebra)@)?:)([ \t]*)(\S.*?)[ \t]*$/gim,
    (_match, head, space, caption) =>
        `${head}${space}<span class="mdcss-tablecap">${caption}</span>`
);

markdown = markdown
    .split("\n")
    .map((line) =>
        mdcssMapProse(line, (prose) =>
            prose.replace(MDCSS_CAPTION_IMG_RE, (match, alt) => {
                const caption = mdcssCaptionOfAlt(alt);
                return caption
                    ? `${match}<span class="mdcss-figcap">${caption}</span>`
                    : match;
            })
        )
    )
    .join("\n");
