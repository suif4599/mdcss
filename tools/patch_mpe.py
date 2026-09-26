#!/usr/bin/env python3
"""Patch markdown-preview-enhanced to keep loading mdcss preview scripts.

crossnote >= 0.9.36 (MPE >= 0.8.36) strips every <script> from head.html.
The designed escape hatch is notebook.trustedScriptRoots — extra
directories whose file-based scripts may run — but MPE never assigns it.
This patch adds the assignment to the compiled applyPreviewScripts
method, pointing at the global crossnote config directory (the same
directory mdcss deploys head.html and mdcss_image_effects.js to).

The injected code resolves that directory at runtime from
XDG_CONFIG_HOME / USERPROFILE / HOME, mirroring MPE's own
getGlobalConfigPath() minus its configPath setting (users of that
setting are not covered), so one patched build works for every user
and inside nix builds.

Manual by design: mdcss never modifies the extension itself. Run this
script yourself, and re-run it after every MPE update (updates replace
the patched file). NixOS and other read-only installs: use the flake
module homeManagerModules.markdown-preview-enhanced (README).

Usage:
  python tools/patch_mpe.py [--extension-dir DIR] [--no-backup]

Also required, in VS Code / VSCodium settings (application scope):
  "markdown-preview-enhanced.enablePreviewScripts": true

Exports (PDF / HTML / eBook) stay script-free in every MPE version:
the export path strips head.html scripts unconditionally.
"""

import argparse
import os
import re
import sys
from pathlib import Path

EXTENSION_GLOB = "shd101wyy.markdown-preview-enhanced-*"
NATIVE_BUNDLE = Path("out/native/extension.js")
# Minified shape shared by MPE 0.8.36-0.8.38 (verified against the
# marketplace builds); the parameter name varies, the method does not.
ANCHOR_RE = re.compile(r"applyPreviewScripts\((\w+)\)\{")
# Only the process global, never a bundler-renamed require; crossnote
# normalizes separators via path.resolve/realpath on both sides of its
# containment check, so forward slashes are fine everywhere.
RUNTIME_ROOT_EXPR = (
    '"win32"===process.platform?'
    '(process.env.USERPROFILE||process.env.HOME||"")+"/.crossnote":'
    'process.env.XDG_CONFIG_HOME?process.env.XDG_CONFIG_HOME+"/crossnote":'
    '(process.env.HOME||"")+"/.local/state/crossnote"'
)


def default_crossnote_dir() -> Path:
    """What RUNTIME_ROOT_EXPR resolves to on this machine."""
    if sys.platform == "win32":
        return Path.home() / ".crossnote"
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        return Path(xdg).resolve() / "crossnote"
    return Path.home() / ".local/state/crossnote"


def find_extension_dir() -> Path:
    roots = [Path.home() / ".vscode/extensions", Path.home() / ".vscode-oss/extensions"]
    matches = [p for root in roots if root.is_dir() for p in root.glob(EXTENSION_GLOB)]
    if not matches:
        searched = ", ".join(str(r) for r in roots)
        sys.exit(f"No MPE extension found under: {searched}\nPass --extension-dir explicitly.")
    def version_key(p: Path) -> list[int]:
        tail = p.name[len(EXTENSION_GLOB) - 1:]
        return [int(x) for x in re.findall(r"\d+", tail)] or [0]
    return max(matches, key=version_key)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--extension-dir", type=Path, default=None,
                        help="MPE extension directory (default: newest match under "
                             "~/.vscode/extensions or ~/.vscode-oss/extensions)")
    parser.add_argument("--no-backup", action="store_true",
                        help="Do not keep extension.js.bak-mdcss (for nix builds)")
    args = parser.parse_args()

    extension_dir = args.extension_dir or find_extension_dir()
    bundle = extension_dir / NATIVE_BUNDLE
    if not bundle.is_file():
        sys.exit(f"Bundle not found: {bundle}")

    try:
        content = bundle.read_text(encoding="utf-8")
    except PermissionError:
        sys.exit(f"Cannot read {bundle}.")

    if 'trustedScriptRoots=["' in content:
        print("Already patched — nothing to do.")
        return
    if "trustedScriptRoots" not in content:
        print("MPE <= 0.8.35 detected (no trustedScriptRoots in the bundle): "
              "no patch needed, inline head.html scripts already survive.")
        return
    anchors = ANCHOR_RE.findall(content)
    if len(anchors) != 1:
        sys.exit(f"Expected exactly one applyPreviewScripts definition, found {len(anchors)}; "
                 "unknown bundle shape — patch not applied.")

    replacement = rf"applyPreviewScripts(\1){{\1.trustedScriptRoots=[{RUNTIME_ROOT_EXPR}];"
    patched = ANCHOR_RE.sub(replacement, content, count=1)
    if f"trustedScriptRoots=[{RUNTIME_ROOT_EXPR}]" not in patched:
        sys.exit("Self-check failed — patch not applied.")

    try:
        if not args.no_backup:
            backup = bundle.with_suffix(".js.bak-mdcss")
            backup.write_text(content, encoding="utf-8")
        bundle.write_text(patched, encoding="utf-8")
    except PermissionError:
        sys.exit(f"Cannot write {bundle} — read-only install (e.g. nix store).\n"
                 "On NixOS, use the mdcss flake module instead:\n"
                 "  inputs.mdcss.homeManagerModules.markdown-preview-enhanced")

    print(f"Patched: {bundle}")
    print(f"Trusted script root resolves at runtime; on this machine: "
          f"{default_crossnote_dir()}")
    print("Next steps:")
    print('  1. Set "markdown-preview-enhanced.enablePreviewScripts": true (user settings)')
    print("  2. Trust the workspace, then Developer: Reload Window")
    print("  3. Re-run this script after every MPE update")


if __name__ == "__main__":
    main()
