// Wraps captioned/row images into <figure> elements.
// postparser_image.js marks images with classes (mdcss-row, mdcss-left, ...)
// and a data-mdcss-cap attribute carrying the raw caption (leading '.' kept
// for auto-numbering); this pass consumes the marker and builds the figures.
function hasMdcssClass(tag, cls) {
    const m = tag.match(/\bclass=(['"])(.*?)\1/i);
    return m ? m[2].split(/\s+/).includes(cls) : false;
}

function rewriteImgStyle(imgTag, style) {
    const styleMatch = imgTag.match(/style=(['"])(.*?)\1/i);
    if (styleMatch) {
        return imgTag.replace(styleMatch[0], `style="${style}"`);
    }
    if (imgTag.endsWith('/>')) {
        return `${imgTag.slice(0, -2)} style="${style}"/>`;
    }
    return `${imgTag.slice(0, -1)} style="${style}">`;
}

html = html.replace(
    /<img[^\>]*>/g,
    (imgTag) => {
        const capMatch = imgTag.match(/\bdata-mdcss-cap="([^"]*)"/i);
        const caption = capMatch ? capMatch[1] : '';
        const isRow = hasMdcssClass(imgTag, 'mdcss-row');
        if (!caption && !isRow) return imgTag;
        // Consume the marker attribute; the caption lives in the figcaption below.
        imgTag = imgTag.replace(/\s+data-mdcss-cap="[^"]*"/, '');

        const isFloat = hasMdcssClass(imgTag, 'mdcss-float-left') || hasMdcssClass(imgTag, 'mdcss-float-right');
        const isSideAligned = !isFloat && (hasMdcssClass(imgTag, 'mdcss-left') || hasMdcssClass(imgTag, 'mdcss-right'));
        const finalCaption = caption.startsWith('.') ? `图@COUNT_PLACEHOLDER@:\t` + caption.slice(1) : caption;
        if (!isRow) {
            if (isFloat) {
                let match = imgTag.match(/style=(['"])(.*?)\1/i);
                let style = match ? match[2] : '';
                style = style.replace(/float:\s*(left|right)\s*!?important?/gi, '');
                style = style.replace(/display:\s*inline-block/g, 'display: block');
                match = style.match(/width:\s*(\d{1,4}(?:px|%))/i);
                const width = match ? match[1] : '100%';
                style = style.replace(/width:\s*\d{1,4}(?:px|%)/g, `width: 100%`);
                if (!/display\s*:/i.test(style)) {
                    style = `${style}; display: block`;
                }
                style = style
                    .split(';')
                    .map((s) => s.trim())
                    .filter(Boolean)
                    .join('; ');
                imgTag = rewriteImgStyle(imgTag, style);
                const floatDir = hasMdcssClass(imgTag, 'mdcss-float-right') ? 'right' : 'left';
                const margin = floatDir === 'left' ? '0 1em 1em 0' : '0 0 1em 1em';
                return `<figure class="mdcss-fig mdcss-fig-float-${floatDir}" style="float: ${floatDir}; width: ${width}; margin: ${margin};">
${imgTag}
<figcaption style="text-align: center; overflow-wrap: break-word;">${finalCaption}</figcaption>
</figure>`;
            }

            if (isSideAligned) {
                let match = imgTag.match(/style=(['"])(.*?)\1/i);
                let style = match ? match[2] : '';
                style = style.replace(/display:\s*inline-block/g, 'display: block');
                match = style.match(/width:\s*(\d{1,4}(?:px|%))/i);
                const width = match ? match[1] : '100%';
                style = style.replace(/width:\s*\d{1,4}(?:px|%)/g, `width: 100%`);
                style = style
                    .split(';')
                    .map((s) => s.trim())
                    .filter(Boolean)
                    .join('; ');
                imgTag = rewriteImgStyle(imgTag, style);

                const margin = hasMdcssClass(imgTag, 'mdcss-right') ? '0 0 1em auto' : '0 auto 1em 0';
                return `<figure class="mdcss-fig" style="width: ${width}; margin: ${margin};">
${imgTag}
<figcaption style="text-align: center; overflow-wrap: break-word;">${finalCaption}</figcaption>
</figure>`;
            }

            return `<figure class="mdcss-fig" style="width: 100%; margin: 0 auto; text-align: center;">
${imgTag}
<figcaption style="text-align: center; overflow-wrap: break-word;">${finalCaption}</figcaption>
</figure>`;
        }
        let match = imgTag.match(/style=(['"])(.*?)\1/i);
        let style = match ? match[2] : '';
        style = style.replace(/display:\s*inline-block/g, 'display: block');
        match = style.match(/width:\s*(\d{1,4}(?:px|%))/i);
        const width = match ? match[1] : '100%';
        style = style.replace(/width:\s*\d{1,4}(?:px|%)/g, `width: 100%`);
        imgTag = rewriteImgStyle(imgTag, style);
        // 子图标题：不参与全局图号，改用 (a)(b)(c) 占位符，在归组时按顺序替换
        const subCaption = caption.startsWith('.') ? `@SUBFIGURE_PLACEHOLDER@\t` + caption.slice(1) : caption;
        return `<figure class="mdcss-fig mdcss-fig-row" style="width: ${width}; margin: 0; display: inline-block; vertical-align: top;">
${imgTag}
    ${subCaption ? `<figcaption style="text-align: center; overflow-wrap: break-word;">${subCaption}</figcaption>` : ''}
</figure>`;
    }
)

// 子图字母编号：0 → a, 1 → b, ..., 25 → z, 26 → aa, 27 → ab ...
function subLabel(n) {
    let label = '';
    n += 1;
    while (n > 0) {
        const rem = (n - 1) % 26;
        label = String.fromCharCode(97 + rem) + label;
        n = Math.floor((n - 1) / 26);
    }
    return label;
}

// Group consecutive row figures into one centered figure; a "(...)" tail in
// the first sub-caption becomes the group's (optionally numbered) title.
html = html.replace(
    /((<figure\b[^>]*\bclass=(?:"[^"]*mdcss-fig-row[^"]*"|'[^']*mdcss-fig-row[^']*')[^>]*>[\s\S]*?<\/figure>\s*)+)/g,
    (match) => {
        let firstFigure = match.split('</figure>')[0];
        let captionMatch = firstFigure.match(/<figcaption.*?>(.*?)<\/figcaption>/i);
        let caption = captionMatch ? captionMatch[1] : '';
        let generalCaptionMatch = caption.match(/\((.+)\)/i);
        let generalCaption = generalCaptionMatch ? generalCaptionMatch[1] : '';
        if (generalCaption) {
            let modifiedCaption = caption.replace( /\((.+)\)/i, "");
            let modifiedCaptionTag = captionMatch[0].replace(caption, modifiedCaption);
            let modifiedFirstFigure = firstFigure.replace(captionMatch[0], modifiedCaptionTag);
            match = match.replace(firstFigure, modifiedFirstFigure);
            generalCaption = generalCaption.startsWith('.') ? `图@COUNT_PLACEHOLDER@:\t` + generalCaption.slice(1) : generalCaption;
            generalCaption = `<figcaption style="text-align: center; overflow-wrap: break-word;">${generalCaption}</figcaption>`;
        }
        // 子图 (a)(b)(c) 编号：每组从 (a) 开始，按组内顺序给带占位符的子图标题编号
        let subIdx = 0;
        match = match.replace(/@SUBFIGURE_PLACEHOLDER@/g, () => `(${subLabel(subIdx++)})`);
        return `<figure class="mdcss-fig-group" style="text-align: center; width: 100%; margin: 0 auto;">
${match}
${generalCaption || ''}
</figure>`;
    }
)

// In flex-column containers, float on sibling blocks will not wrap text.
// Merge "float figure + next paragraph" into one paragraph so wrapping still works.
html = html.replace(
    /(?:<p>\s*<\/p>\s*)?(<figure\b[^>]*\bclass=(['"])[^'"]*mdcss-fig-float-(?:left|right)[^'"]*\2[^>]*>[\s\S]*?<\/figure>)\s*(?:<p>\s*<\/p>\s*)?<p>([\s\S]*?)<\/p>/g,
    (match, figureHtml, _q, nextParagraphContent) => `<p>${figureHtml}${nextParagraphContent}</p>`
)

let cnt = 0;
html = html.replace(/@COUNT_PLACEHOLDER@/g, (match) => {
    cnt += 1;
    return cnt;
});
