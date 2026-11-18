# Visual tests

Rendering tests use the same engine as VS Code + Markdown Preview Enhanced: crossnote renders the note (loading the mdcss `style.less` / `parser.js` / `head.html` artifacts from a temporary `.crossnote` directory), and the pinned Playwright Chromium prints crossnote's print template to PDF. Each page is converted to SVG and compared pixel by pixel with the committed `expected.<n>.svg`.

## Setup

One-time, from the repository root:

```bash
pixi install -e visual
pixi run -e visual visual-setup
```

`visual-setup` installs the pnpm dependencies in this directory and downloads the Chromium build pinned by the installed Playwright version. The default environment is unaffected: plain `pixi install` does not install any of this.

## Commands

```bash
pixi run -e visual visual-test        # render every case and compare
pixi run -e visual visual-bless       # rewrite expected.<n>.svg from the current render
pixi run -e visual visual-bless 000-placeholder   # only selected cases
```

`visual-bless` only writes references; inspect the SVGs before committing them. The references become the regression baseline. Every new feature needs a case, and every fix needs a case that fails without the fix.

## Cases

```
cases/<name>/
  input.md          # markdown under test, ASCII only
  options.json      # optional; at most ONE leaf may differ from config/base.json
  expected.1.svg    # one file per page, produced by visual-bless
```

`config/base.json` contains every mdcss generator parameter plus the locked crossnote renderer options. A feature case changes exactly one parameter (for example `{"mdcss": {"font_size": "18px"}}`); a plain regression case changes none. More than one difference is rejected.

Test documents must be ASCII. Only English fonts are used (`DejaVuSans.ttf`, `SourceCodePro-Regular.ttf` from the pinned conda packages); no CJK coverage is expected from this suite.

Images, when cases need them, must be copied into the notebook directory by the harness so the export HTML stays local (network access is not part of the render).

## Comparison

A rendered pixel `(i, j)` passes when some reference pixel `(i+dy, j+dx)` with `dy, dx` in `[-delta_x, delta_x]` has a per-channel difference of at most `delta_color`. A page passes only when every rendered pixel passes; page count and page size must match exactly. Defaults are `delta_color=12`, `delta_x=2`, `dpi=144` (see `config/base.json`).

Failures leave `actual.pdf`, `page-*.svg`, `actual-*.png`, `expected-*.png` and `diff-*.png` in `out/<case>/`.

## Version pinning

- `pixi.lock` pins Playwright, PyMuPDF, NumPy, Pillow, pnpm, Node.js and the two test font packages for linux-64 and win-64.
- `pnpm-lock.yaml` pins crossnote and its full dependency tree (markdown-it, KaTeX, Prism, …).
- `config/browser.json` records the Chromium build derived from the pinned Playwright version. The harness checks it before rendering and fails with an explicit message when Playwright or Chromium differs, so a browser upgrade requires re-blessing the references.
- The harness prepends the pixi environment's `lib` to `LD_LIBRARY_PATH` on Linux so the downloaded Chromium finds its shared libraries.

No version is supplied through Nix.
