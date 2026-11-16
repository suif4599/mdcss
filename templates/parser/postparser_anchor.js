// Resolve in-page fragment links against the heading ids the renderer
// actually produced. crossnote turns some CJK punctuation into "-" in the id
// ("三、标题" -> "三-标题"), while a hand-written link usually drops it
// ("#三标题"); markdown-it additionally percent-encodes non-ASCII fragments.
// The browser compares the decoded fragment with the raw id, so such a small
// slug difference silently makes the link a no-op (and the PDF export writes a
// destination for an anchor that does not exist). Match both forms by a
// punctuation-insensitive key and rewrite the href to the real id. Links with
// no matching heading (footnotes, custom ids on non-heading elements) are left
// untouched.
//
// Auto-numbered headings ("## .标题" -> "二、标题") put the number in the id,
// but the number depends on the chapter order: a link that repeats it breaks
// whenever a section moves. Their title without the numbering ("#标题") is
// therefore registered as an alias too, and only used when exactly one
// heading claims it — duplicated section names ("概述" in several chapters)
// still need the numbered form to stay unambiguous.
function mdcssAnchorText(value) {
    let text = value;
    try {
        text = decodeURIComponent(text);
    } catch (error) {
        // Keep the raw fragment when it is not valid percent encoding.
    }
    return text
        .replace(/&lt;/g, "<")
        .replace(/&gt;/g, ">")
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&amp;/g, "&");
}

function mdcssAnchorKey(value) {
    let text = mdcssAnchorText(value);
    if (typeof text.normalize === "function") {
        text = text.normalize("NFKC");
    }
    return text.toLowerCase().replace(/[^\p{L}\p{N}\p{M}]+/gu, "");
}

// Strip the numbering tokens the mappers can prepend: "二、", "1.", "1.1 "
// (crossnote keeps the zero-width space number() emits), "a)", "i)". Only one
// token group is removed: a title that itself starts with a number ("一、2026
// 计划") keeps it.
function mdcssAnchorBareTitle(value) {
    return mdcssAnchorText(value)
        .replace(/^[\s\u200B]+/u, "")
        .replace(/^[零一二三四五六七八九十百千两]+、/u, "")
        .replace(/^\d+\u200B?(?:[.．]\u200B?\d+\u200B?)+[.．]?/u, "")
        .replace(/^\d+\u200B?[.．]\u200B?/u, "")
        .replace(/^[A-Za-z]{1,8}[)）]/u, "");
}

const mdcssHeadingAnchors = [];
html.replace(/<h([1-6])\b([^>]*)>([\s\S]*?)<\/h\1>/gi, (match, level, attributes, inner) => {
    const idMatch = /\sid=(["'])([\s\S]*?)\1/i.exec(attributes);
    if (!idMatch) return match;
    const id = mdcssAnchorText(idMatch[2]);
    const key = mdcssAnchorKey(id);
    const bare = mdcssAnchorKey(mdcssAnchorBareTitle(inner.replace(/<[^>]*>/g, "")));
    mdcssHeadingAnchors.push({ id: id, key: key, bare: bare !== key ? bare : "" });
    return match;
});

const mdcssBareHeadingCounts = new Map();
mdcssHeadingAnchors.forEach((heading) => {
    if (!heading.bare) return;
    mdcssBareHeadingCounts.set(heading.bare, (mdcssBareHeadingCounts.get(heading.bare) || 0) + 1);
});

if (mdcssHeadingAnchors.length) {
    html = html.replace(/(<a\b[^>]*?\shref=)(["'])#([^"']*)\2/gi, (match, head, quote, fragment) => {
        if (!fragment) return match;
        const decoded = mdcssAnchorText(fragment);
        let target = mdcssHeadingAnchors.find((heading) => heading.id === decoded);
        if (!target) {
            const key = mdcssAnchorKey(decoded);
            if (key) {
                target = mdcssHeadingAnchors.find((heading) => heading.key === key);
            }
            if (!target && mdcssBareHeadingCounts.get(key) === 1) {
                target = mdcssHeadingAnchors.find((heading) => heading.bare === key);
            }
        }
        if (!target) return match;
        return `${head}${quote}#${encodeURIComponent(target.id)}${quote}`;
    });
}
