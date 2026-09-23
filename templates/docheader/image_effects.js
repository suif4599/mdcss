// Runtime canvas processor for the I/M image effects (MPE preview).
//
// Each image is transformed once, per pixel, at its NATIVE resolution into
// a canvas, and the canvas becomes the img's new src — so display goes
// through the exact same path as an unfiltered image.
//
// Band semantics (256-entry luma LUTs with KNEE-wide linear knees; the
// bounds literals below are the configured defaults):
//   I (mdcss-bright[-lo-hi]) : mirror pixels with luma <= lo or >= hi
//                              (channel differences, hence hue, preserved)
//   M (mdcss-matte[-lo-hi])  : brighten luma <= lo the same way; make
//                              luma >= hi transparent; mid band untouched
//
// Reading pixels requires a CORS-clean canvas: we first try the image as
// loaded, then retry through a crossOrigin="anonymous" reload (VSCode
// webview resources serve CORS headers). If both fail (e.g. plain
// file:// pages), the image is left as-is — there is no fallback path.
//
// The Inkstone emission replaces THEME_GATED with true: the effects then
// follow the page theme (they apply only under :root[data-theme='dark']
// and the original src is restored on light), and processed URLs are
// cached, because the Inkstone preview re-creates every <img> on each
// debounced re-render.
(function () {
    var KNEE = 4;
    // Fringe handling: antialiased strokes (thin lines especially) have
    // per-pixel luma that wobbles across the band threshold, so a strictly
    // per-pixel decision splits one stroke into black and white patches.
    // Band membership and the mirror center therefore follow the LOCAL
    // BACKGROUND — min/max filtered luma over a FRINGE-pixel window: the
    // darkest point of a stroke decides for the whole stroke, and mirroring
    // around it (c' = 255 + c - 2*bg) maps core and antialiasing through
    // one continuous field. FRINGE is kept at 1 so the transformed halo
    // around dark content stays one source pixel wide (a quarter display
    // pixel at 4x downscale), keeping the affected area tight.
    var FRINGE = 1;
    // Foreground tolerance for the BRIGHT band: a pixel much darker than
    // its local bright background (dark strokes on white) is foreground —
    // its matte/mirror weight fades to zero so thin strokes are not matted
    // out by the white background showing through the max-filter window
    // (their color is already handled by the dark branch). The dark band
    // has no such fade: partial-weight mirroring would park antialiased
    // edges at mid-gray again.
    var FG_TOL = 96;
    // The literals below are replaced at build time: the [lo, hi] bounds
    // with the configured --invert-bounds / --matte-bounds defaults, and
    // THEME_GATED with true for the Inkstone emission (theme-follow mode).
    var INVERT_BOUNDS = [32, 239];
    var MATTE_BOUNDS = [64, 239];
    var THEME_GATED = false;

    // Processed data URLs cached per effect + bounds + source URL: the
    // Inkstone preview re-creates every <img> on each debounced re-render,
    // so without a cache each commit would re-download and re-transform
    // every I/M image. Insertion-order LRU; only successful results are
    // cached.
    var CACHE = new Map();
    var CACHE_CAP = 16;

    var EFFECT_SELECTOR = 'img.mdcss-bright, img.mdcss-matte, img[class*="mdcss-bright-"], img[class*="mdcss-matte-"]';

    function isDark() {
        return document.documentElement.dataset.theme === 'dark';
    }

    // Undo the swap on a processed image: back to the original src and a
    // clean processing state, keeping the effect class so a later dark
    // theme re-applies the (cached) transform.
    function restore(img) {
        if (img.dataset.mdcssSrc !== undefined) {
            img.src = img.dataset.mdcssSrc;
            delete img.dataset.mdcssSrc;
        }
        delete img.dataset.mdcssFx;
    }

    function cacheKey(fx, src) {
        return fx.kind + '|' + fx.lo + ',' + fx.hi + '|' + src;
    }

    function cachePut(key, url) {
        CACHE.delete(key);
        CACHE.set(key, url);
        if (CACHE.size > CACHE_CAP) CACHE.delete(CACHE.keys().next().value);
    }

    function darkTable(lo) {
        var t = new Float32Array(256);
        for (var i = 0; i <= 255; i++) {
            t[i] = i <= lo ? 1 : i >= lo + KNEE ? 0 : 1 - (i - lo) / KNEE;
        }
        return t;
    }

    function brightTable(hi) {
        var t = new Float32Array(256);
        for (var j = 0; j <= 255; j++) {
            t[j] = j >= hi ? 1 : j <= hi - KNEE ? 0 : (j - (hi - KNEE)) / KNEE;
        }
        return t;
    }

    function lut(t, luma) {
        var x = luma < 0 ? 0 : luma > 255 ? 255 : luma;
        var i = x | 0;
        var f = x - i;
        return i >= 255 ? t[255] : t[i] * (1 - f) + t[i + 1] * f;
    }

    // Separable min/max filter over a (2*FRINGE+1) window: pass isMin=true
    // for the local dark background, false for the local bright one.
    function localBackground(src, w, h, isMin) {
        var tmp = new Float32Array(w * h);
        var out = new Float32Array(w * h);
        var x, y, k, v, a, b;
        for (y = 0; y < h; y++) {
            var row = y * w;
            for (x = 0; x < w; x++) {
                v = src[row + x];
                for (k = 1; k <= FRINGE; k++) {
                    a = x - k >= 0 ? src[row + x - k] : v;
                    b = x + k < w ? src[row + x + k] : v;
                    if (isMin ? a < v : a > v) v = a;
                    if (isMin ? b < v : b > v) v = b;
                }
                tmp[row + x] = v;
            }
        }
        for (x = 0; x < w; x++) {
            for (y = 0; y < h; y++) {
                v = tmp[y * w + x];
                for (k = 1; k <= FRINGE; k++) {
                    a = y - k >= 0 ? tmp[(y - k) * w + x] : v;
                    b = y + k < h ? tmp[(y + k) * w + x] : v;
                    if (isMin ? a < v : a > v) v = a;
                    if (isMin ? b < v : b > v) v = b;
                }
                out[y * w + x] = v;
            }
        }
        return out;
    }

    var CLASS_RE = /(^|\s)(mdcss-(bright|matte)(-(\d{1,3})-(\d{1,3}))?)(?=\s|$)/;

    function effectOf(img) {
        var m = (img.getAttribute('class') || '').match(CLASS_RE);
        if (!m) return null;
        var kind = m[3];
        var lo = m[5] !== undefined ? Math.round(Number(m[5])) : null;
        var hi = m[6] !== undefined ? Math.round(Number(m[6])) : null;
        if (lo !== null && !(0 <= lo && lo < hi && hi <= 255)) { lo = null; hi = null; }
        var def = kind === 'bright' ? INVERT_BOUNDS : MATTE_BOUNDS;
        return {
            kind: kind,
            cls: m[2],
            lo: lo === null ? def[0] : lo,
            hi: lo === null ? def[1] : hi,
        };
    }

    // In-place pixel transform (RGBA interleaved): the heart of both
    // effects, kept DOM-free so it can be unit-tested under node.
    function transformPixels(px, lumaBuf, bgDark, bgBright, kind, dark, bright) {
        var isBright = kind === 'bright';
        for (var p = 0; p < lumaBuf.length; p++) {
            var o = p * 4;
            var r = px[o], g = px[o + 1], b = px[o + 2];
            // background-driven band weights; the bright band exempts
            // pixels far darker than their local bright background
            var wD = lut(dark, bgDark[p]);
            var fgB = 1 - (bgBright[p] - lumaBuf[p]) / FG_TOL;
            if (fgB < 0) fgB = 0; else if (fgB > 1) fgB = 1;
            var wB = lut(bright, bgBright[p]) * fgB;
            if (wD > 0) {
                // mirror around the local background: luma -> 255 - bg,
                // content keeps its offset from the background
                var dr = 255 + r - 2 * bgDark[p], dg = 255 + g - 2 * bgDark[p],
                    db = 255 + b - 2 * bgDark[p];
                px[o] = wD * (dr < 0 ? 0 : dr > 255 ? 255 : dr) + (1 - wD) * r;
                px[o + 1] = wD * (dg < 0 ? 0 : dg > 255 ? 255 : dg) + (1 - wD) * g;
                px[o + 2] = wD * (db < 0 ? 0 : db > 255 ? 255 : db) + (1 - wD) * b;
            }
            if (isBright && wB > 0) {
                var br = 255 + r - 2 * bgBright[p], bg2 = 255 + g - 2 * bgBright[p],
                    bb = 255 + b - 2 * bgBright[p];
                px[o] += wB * ((br < 0 ? 0 : br > 255 ? 255 : br) - r);
                px[o + 1] += wB * ((bg2 < 0 ? 0 : bg2 > 255 ? 255 : bg2) - g);
                px[o + 2] += wB * ((bb < 0 ? 0 : bb > 255 ? 255 : bb) - b);
            }
            if (kind === 'matte') {
                var keep = 1 - wB;
                if (keep < 1) px[o + 3] = px[o + 3] * keep;
            }
        }
    }

    // Transform `source` (a decoded, drawable image) per `fx`; returns a PNG
    // data URL, or null when the canvas is tainted (SecurityError).
    function transform(fx, source) {
        var dark = darkTable(fx.lo);
        var bright = brightTable(fx.hi);
        var w = source.naturalWidth || source.width;
        var h = source.naturalHeight || source.height;
        var canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        var ctx = canvas.getContext('2d', { willReadFrequently: true });
        ctx.drawImage(source, 0, 0);
        var data;
        try {
            data = ctx.getImageData(0, 0, w, h);
        } catch (e) {
            return null;
        }
        var px = data.data;
        var n = w * h;
        var lumaBuf = new Float32Array(n);
        for (var i = 0; i < n; i++) {
            var q = i * 4;
            lumaBuf[i] = 0.299 * px[q] + 0.587 * px[q + 1] + 0.114 * px[q + 2];
        }
        var bgDark = localBackground(lumaBuf, w, h, true);
        var bgBright = localBackground(lumaBuf, w, h, false);
        transformPixels(px, lumaBuf, bgDark, bgBright, fx.kind, dark, bright);
        ctx.putImageData(data, 0, 0);
        try {
            return canvas.toDataURL('image/png');
        } catch (e) {
            return null;
        }
    }

    function processImage(img) {
        var fx = effectOf(img);
        if (!fx || img.dataset.mdcssFx === 'busy') return;
        if (THEME_GATED && !isDark()) {
            restore(img);
            return;
        }
        if (img.dataset.mdcssFx === 'done' || img.dataset.mdcssFx === 'failed') return;
        if (!img.src || img.src.slice(0, 5) === 'data:') return;
        if (!img.complete || img.naturalWidth === 0) {
            img.dataset.mdcssFx = 'busy';
            img.addEventListener('load', function () { delete img.dataset.mdcssFx; processImage(img); }, { once: true });
            img.addEventListener('error', function () { delete img.dataset.mdcssFx; }, { once: true });
            return;
        }
        img.dataset.mdcssFx = 'busy';
        var src = img.src;

        function finish(url) {
            if (!url) {
                // unreadable pixels: leave as-is, and do not retry within
                // this DOM generation
                img.dataset.mdcssFx = 'failed';
                return;
            }
            if (THEME_GATED && !isDark()) {
                // the theme flipped to light while the transform was in
                // flight: the swap would be wrong, restore instead
                restore(img);
                return;
            }
            cachePut(cacheKey(fx, src), url);
            if (img.dataset.mdcssSrc === undefined) img.dataset.mdcssSrc = src;
            img.src = url;
            img.dataset.mdcssFx = 'done';
        }

        var hit = CACHE.get(cacheKey(fx, src));
        if (hit !== undefined) { finish(hit); return; }
        var url = transform(fx, img);
        if (url !== null) { finish(url); return; }
        // The as-loaded image taints the canvas — retry through a CORS-clean
        // reload of the same URL (a no-op download thanks to caching).
        var probe = new Image();
        probe.crossOrigin = 'anonymous';
        probe.onload = function () { finish(transform(fx, probe)); };
        probe.onerror = function () { finish(null); };
        probe.src = src;
    }

    function scan(root) {
        var imgs = (root || document).querySelectorAll(EFFECT_SELECTOR);
        for (var i = 0; i < imgs.length; i++) processImage(imgs[i]);
    }

    function boot() {
        scan(document);
        var observer = new MutationObserver(function (muts) {
            for (var i = 0; i < muts.length; i++) {
                var added = muts[i].addedNodes;
                for (var j = 0; j < added.length; j++) {
                    var n = added[j];
                    if (n.nodeType !== 1) continue;
                    if (n.tagName === 'IMG') processImage(n);
                    else if (n.querySelectorAll) scan(n);
                }
            }
        });
        observer.observe(document.body || document.documentElement, { childList: true, subtree: true });
        if (THEME_GATED) {
            // Theme flips do not re-create the DOM in Inkstone: watch the
            // root data-theme attribute and swap srcs both ways — dark
            // re-applies (a cache hit is instant), light restores.
            var themeObserver = new MutationObserver(function () {
                if (isDark()) { scan(document); return; }
                var imgs = document.querySelectorAll(EFFECT_SELECTOR);
                for (var i = 0; i < imgs.length; i++) restore(imgs[i]);
            });
            themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
        }
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', boot);
        } else {
            boot();
        }
    }

    // Exposed for the node-based unit tests (tests/test_docheader.py);
    // a no-op in browsers, where `module` is undefined.
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            KNEE: KNEE,
            FRINGE: FRINGE,
            FG_TOL: FG_TOL,
            INVERT_BOUNDS: INVERT_BOUNDS,
            MATTE_BOUNDS: MATTE_BOUNDS,
            darkTable: darkTable,
            brightTable: brightTable,
            lut: lut,
            localBackground: localBackground,
            transformPixels: transformPixels,
        };
    }
})();
