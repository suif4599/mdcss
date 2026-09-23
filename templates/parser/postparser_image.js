// Image alt control syntax: ![control|caption|alt](src)
//   control := WIDTH [UNIT] [LAYOUT] [EFFECT [BOUNDS]]  (may be empty)
//   WIDTH   := 1-4 digits; UNIT := % (default, capped at 100) | px (uncapped)
//   LAYOUT  := r | L | R | Lf | Rf (mutually exclusive)
//   EFFECT  := i | I | m | M (mutually exclusive)
//   BOUNDS  := (lo,hi) — optional per-image luma thresholds (8-bit) for I/M,
//              e.g. I(10,253) or M(5,250). Invalid bounds fall back to the
//              global defaults (plain I/M behavior).
// An alt whose first pipe field does not match this grammar (and is not empty)
// is a real alt text: the image is left completely untouched.
// The I/M classes (mdcss-bright / mdcss-matte, optionally with the -lo-hi
// suffix) are picked up by the runtime canvas processor in head.html
// (templates/docheader/image_effects.js), which transforms the pixels and
// swaps in the result as the new image src.
const MDCSS_CONTROL_RE = /^(\d{1,4})(%|px)?(Lf|Rf|r|L|R)?(i|I|m|M)?(?:\((\d{1,3}),(\d{1,3})\))?$/;
const MDCSS_LAYOUT_CLASS = {
    r: 'mdcss-row',
    L: 'mdcss-left',
    R: 'mdcss-right',
    Lf: 'mdcss-float-left',
    Rf: 'mdcss-float-right',
};
const MDCSS_EFFECT_CLASS = {
    i: 'mdcss-inv',
    I: 'mdcss-bright',
    m: 'mdcss-mix',
    M: 'mdcss-matte',
};

function parseImageAlt(alt) {
    if (!alt) return null;
    const parts = alt.split('|');
    const control = parts[0].trim();
    let match = null;
    if (control !== '') {
        match = control.match(MDCSS_CONTROL_RE);
        // Non-matching first field (e.g. plain English alt) => real alt text.
        if (!match || Number(match[1]) <= 0) return null;
    }
    let lo = null;
    let hi = null;
    if (match && match[5] !== undefined) {
        const a = Number(match[5]);
        const b = Number(match[6]);
        if (0 <= a && a < b && b <= 255) {
            lo = a;
            hi = b;
        }
    }
    return {
        width: match ? Number(match[1]) : null,
        unit: match ? (match[2] || '%') : null,
        layout: match ? (match[3] || null) : null,
        effect: match ? (match[4] || null) : null,
        effectLo: lo,
        effectHi: hi,
        caption: (parts[1] || '').trim(),
        // Everything from the third pipe field on belongs to the real alt
        // (the real alt itself may contain pipes).
        realAlt: parts.slice(2).join('|').trim(),
    };
}

function widthValueOf(parsed) {
    if (parsed.width === null) return null;
    if (parsed.unit === 'px') return `${parsed.width}px`;
    return `${Math.min(parsed.width, 100)}%`;
}

function mergeStyle(existingStyle, widthValue, layout) {
    const styleMap = new Map();
    const styleText = existingStyle || '';

    styleText
        .split(';')
        .map((s) => s.trim())
        .filter(Boolean)
        .forEach((entry) => {
            const idx = entry.indexOf(':');
            if (idx <= 0) return;
            const key = entry.slice(0, idx).trim().toLowerCase();
            const value = entry.slice(idx + 1).trim();
            if (!key || !value) return;
            styleMap.set(key, value);
        });

    styleMap.set('width', `${widthValue} !important`);
    styleMap.set('height', 'auto !important');

    // Clear conflicting keys before applying our layout intent.
    styleMap.delete('margin');
    styleMap.delete('margin-left');
    styleMap.delete('margin-right');
    styleMap.delete('vertical-align');

    if (layout === 'r') {
        styleMap.set('display', 'inline-block !important');
        styleMap.set('margin', '0 !important');
        styleMap.set('vertical-align', 'middle !important');
    } else if (layout === 'L') {
        styleMap.set('display', 'block !important');
        styleMap.set('margin-left', '0 !important');
        styleMap.set('margin-right', 'auto !important');
    } else if (layout === 'R') {
        styleMap.set('display', 'block !important');
        styleMap.set('margin-left', 'auto !important');
        styleMap.set('margin-right', '0 !important');
    } else if (layout === 'Lf' || layout === 'Rf') {
        // Float mode: keep width/height only; float comes from the CSS class.
        styleMap.delete('display');
    } else {
        // No layout token: centered block, matching the CSS fallback rules.
        styleMap.set('display', 'block !important');
        styleMap.set('margin', '0 auto !important');
    }

    return Array.from(styleMap.entries())
        .map(([k, v]) => `${k}: ${v}`)
        .join('; ');
}

function appendAttr(imgTag, attrText) {
    if (imgTag.endsWith('/>')) {
        return `${imgTag.slice(0, -2)} ${attrText}/>`;
    }
    return `${imgTag.slice(0, -1)} ${attrText}>`;
}

function mergeClassAttr(imgTag, newClasses) {
    const classMatch = imgTag.match(/\bclass=(['"])(.*?)\1/i);
    if (classMatch) {
        const merged = classMatch[2].split(/\s+/).filter(Boolean);
        newClasses.forEach((c) => {
            if (!merged.includes(c)) merged.push(c);
        });
        return imgTag.replace(classMatch[0], `class="${merged.join(' ')}"`);
    }
    return appendAttr(imgTag, `class="${newClasses.join(' ')}"`);
}

html = html.replace(/<img\b[^>]*>/gi, (imgTag) => {
    const altMatch = imgTag.match(/\balt=(['"])(.*?)\1/i);
    const alt = altMatch ? altMatch[2] : '';
    const parsed = parseImageAlt(alt);
    if (!parsed) return imgTag;

    const widthValue = widthValueOf(parsed);
    const classes = [];
    if (parsed.layout) classes.push(MDCSS_LAYOUT_CLASS[parsed.layout]);
    if (parsed.effect) {
        if (parsed.effectLo !== null) {
            classes.push(`${MDCSS_EFFECT_CLASS[parsed.effect]}-${parsed.effectLo}-${parsed.effectHi}`);
        } else {
            classes.push(MDCSS_EFFECT_CLASS[parsed.effect]);
        }
    }
    if (widthValue === null && !parsed.caption) return imgTag;

    let tag = imgTag;
    if (widthValue !== null) {
        const styleMatch = tag.match(/\bstyle=(['"])(.*?)\1/i);
        const mergedStyle = mergeStyle(styleMatch ? styleMatch[2] : '', widthValue, parsed.layout);
        if (styleMatch) {
            tag = tag.replace(styleMatch[0], `style="${mergedStyle}"`);
        } else {
            tag = appendAttr(tag, `style="${mergedStyle}"`);
        }
    }
    if (classes.length) {
        tag = mergeClassAttr(tag, classes);
    }

    // The output alt carries no control tokens: real alt, else caption, else empty.
    const outAlt = parsed.realAlt || parsed.caption.replace(/^\./, '') || '';
    if (altMatch) {
        tag = tag.replace(altMatch[0], `alt=${altMatch[1]}${outAlt}${altMatch[1]}`);
    }

    // Hand the raw caption (leading '.' kept for numbering) to postparser_imagetitle.js.
    if (parsed.caption) {
        tag = appendAttr(tag, `data-mdcss-cap="${parsed.caption.replace(/"/g, '&quot;')}"`);
    }
    return tag;
});
