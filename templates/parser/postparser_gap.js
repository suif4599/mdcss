// Rebuild the spacer height after sanitization: Inkstone's DOMPurify strips
// inline styles, so the pre pass emits only class + data-* attributes and the
// height is applied here. The 1.6em declaration is the fallback for engines
// without the lh unit; the later lh declaration wins where supported.
function __mdcssGapStyle(value) {
    const match = /^(\d+(?:\.\d+)?)lh$/i.exec(value);
    if (!match) {
        return `height: ${value} !important;`;
    }
    if (Number(match[1]) === 1) {
        return "height: 1.6em !important; height: 1lh !important;";
    }
    return `height: calc(1.6em * ${match[1]}) !important; height: calc(1lh * ${match[1]}) !important;`;
}

html = html.replace(
    /<div\b([^>]*\bclass="mdcss-gap"[^>]*)>\s*<\/div>/g,
    (match, attrs) => {
        const data = /\bdata-mdcss-gap="([^"]*)"/.exec(attrs);
        if (!data || !/^\d+(?:\.\d+)?(?:lh|em|rem|px|pt)$/i.test(data[1])) {
            return match;
        }
        const style = __mdcssGapStyle(data[1]);
        const cleaned = attrs.replace(/\sstyle="[^"]*"/g, "");
        return `<div${cleaned} style="${style}"></div>`;
    },
);
