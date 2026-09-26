"""Tests for tools/patch_mpe.py."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import patch_mpe  # noqa: E402

BUNDLE_0836 = (
    "class A{applyPreviewScripts(t){t.previewScriptsEnabled=W.workspace.isTrusted"
    '&&(U("enablePreviewScripts")??!1)}}'
    "class B{constructor(){this.previewScriptsEnabled=!1,this.trustedScriptRoots=[],"
    "this.notes={}}}"
)
BUNDLE_0835 = (
    "class A{applyPreviewScripts(t){t.previewScriptsEnabled=W.workspace.isTrusted"
    '&&(U("enablePreviewScripts")??!1)}}'
)


@pytest.fixture
def extension_dir(tmp_path: Path) -> Path:
    ext = tmp_path / "shd101wyy.markdown-preview-enhanced-0.8.38"
    (ext / "out/native").mkdir(parents=True)
    (ext / "out/native/extension.js").write_text(BUNDLE_0836, encoding="utf-8")
    return ext


def run_patch(extension_dir: Path, *extra: str) -> None:
    sys.argv = ["patch_mpe.py", "--extension-dir", str(extension_dir), *extra]
    patch_mpe.main()


class TestPatch:
    def test_injects_runtime_root_expression(self, extension_dir: Path, tmp_path: Path) -> None:
        run_patch(extension_dir)
        patched = (extension_dir / "out/native/extension.js").read_text(encoding="utf-8")
        assert f"trustedScriptRoots=[{patch_mpe.RUNTIME_ROOT_EXPR}]" in patched
        assert str(tmp_path) not in patched
        assert patched.index("trustedScriptRoots") < patched.index("previewScriptsEnabled=W")

    def test_creates_backup(self, extension_dir: Path) -> None:
        run_patch(extension_dir)
        backup = extension_dir / "out/native/extension.js.bak-mdcss"
        assert backup.read_text(encoding="utf-8") == BUNDLE_0836

    def test_no_backup_flag(self, extension_dir: Path) -> None:
        run_patch(extension_dir, "--no-backup")
        assert not (extension_dir / "out/native/extension.js.bak-mdcss").exists()

    def test_idempotent(self, extension_dir: Path, capsys) -> None:
        run_patch(extension_dir)
        run_patch(extension_dir)
        patched = (extension_dir / "out/native/extension.js").read_text(encoding="utf-8")
        assert patched.count('trustedScriptRoots=["') == 1
        assert "Already patched" in capsys.readouterr().out

    def test_old_mpe_needs_no_patch(self, tmp_path: Path, capsys) -> None:
        ext = tmp_path / "ext"
        (ext / "out/native").mkdir(parents=True)
        (ext / "out/native/extension.js").write_text(BUNDLE_0835, encoding="utf-8")
        run_patch(ext)
        content = (ext / "out/native/extension.js").read_text(encoding="utf-8")
        assert content == BUNDLE_0835
        assert "no patch needed" in capsys.readouterr().out

    def test_unknown_bundle_shape_refuses(self, tmp_path: Path) -> None:
        ext = tmp_path / "ext"
        (ext / "out/native").mkdir(parents=True)
        (ext / "out/native/extension.js").write_text(
            "class A{constructor(){this.trustedScriptRoots=[]}}", encoding="utf-8"
        )
        with pytest.raises(SystemExit, match="unknown bundle shape"):
            run_patch(ext)

    def test_missing_bundle_refuses(self, tmp_path: Path) -> None:
        ext = tmp_path / "ext"
        ext.mkdir()
        with pytest.raises(SystemExit, match="Bundle not found"):
            run_patch(ext)
