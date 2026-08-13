"""One runnable check. Fails if the compiler, IR, or emitters break."""
from pathlib import Path

from oneread.compile import CONTRACTIONS, PHRASES, compile_text
from oneread.emit import EMITTERS, emit
from oneread.ir import to_ir
from oneread.lint import RULE_IDS, lint, self_test

ROOT = Path(__file__).resolve().parents[1]


def test_linter_self_test():
    self_test()


def test_compile_drops_courtesy_and_contraction():
    result = compile_text("Please set up the cluster; it's ready.", "procedural")
    low = result["compiled"].lower()
    assert "please" not in low
    assert "configure" in low
    assert "it is" in low
    assert result["after"]["violations_total"] < result["before"]["violations_total"]


def test_compile_leaves_a_readable_sentence():
    """A rewrite may not drop a capital, break a verb form, or leave a stump."""
    out = compile_text(
        "Oops! It's simply a robust cache. By leveraging retries it is crucial. "
        "There is a plethora of options and it didn't start.",
        "descriptive",
    )["compiled"]
    assert out.startswith("It is a cache."), out
    assert "By using retries" in out, out
    assert "it is crucial" in out, out
    assert "many options" in out, out
    assert "did not start" in out, out


def test_ir_has_passages_and_disclaimer():
    ir = to_ir("The service retries a failed upload automatically.", "descriptive", source="t.md")
    assert ir["orir"] == "1.0"
    assert ir["passages"]
    assert "asd-ste100.org" in ir["disclaimer"]


def test_every_emitter_returns_text():
    text = Path(ROOT / "fixtures/compiled/error.md").read_text()
    ir = to_ir(text, "procedural", source="error.md")
    ir["findings"] = lint(text, "procedural")["findings"]
    for target in EMITTERS:
        out = emit(target, ir=ir, text_type="procedural", source="error.md")
        assert isinstance(out, str) and len(out) > 10, target


def test_slop_fixtures_are_dirtier_than_compiled():
    slop_dir = ROOT / "fixtures/slop"
    compiled_dir = ROOT / "fixtures/compiled"
    for name in ("readme.md", "error.md", "runbook.md", "openapi.md", "incident.md"):
        slop = lint((slop_dir / name).read_text(), "descriptive")
        clean = lint((compiled_dir / name).read_text(), "descriptive")
        assert slop["violations_total"] > clean["violations_total"], name


def test_code_spans_survive_compile():
    src = "Please set `DB_PASSWORD` prior to connect."
    out = compile_text(src, "procedural")["compiled"]
    assert "`DB_PASSWORD`" in out


def test_playground_mirrors_the_python_rules():
    """The browser and the CLI must fail the same text. Drift here is a bug."""
    raw = (ROOT / "playground/linter.js").read_text()
    js = raw.replace(r"\/", "/").replace(r"\b", "")
    for key in RULE_IDS:
        assert f'"{key}"' in raw, f"playground linter is missing rule key {key}"
    for rx, _ in CONTRACTIONS + PHRASES:
        needle = rx.pattern.replace(r"\b", "").split("(?!")[0]
        assert needle in js, f"playground compiler is missing rewrite {rx.pattern}"


if __name__ == "__main__":
    test_linter_self_test()
    test_compile_drops_courtesy_and_contraction()
    test_compile_leaves_a_readable_sentence()
    test_ir_has_passages_and_disclaimer()
    test_every_emitter_returns_text()
    test_slop_fixtures_are_dirtier_than_compiled()
    test_code_spans_survive_compile()
    test_playground_mirrors_the_python_rules()
    print("tests OK")
