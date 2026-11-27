"""Leak gate tests (plan §7.14, Task 1.7). Positive fixtures are assembled from
fragments at runtime so that no committed file carries a real-looking leak."""
import os
import pathlib
import subprocess
import sys

import pytest

from engine import leakcheck

ROOT = pathlib.Path(__file__).resolve().parents[1]
AT = "@"
HOME = "/" + "Users" + "/alice/project"
LINUX_HOME = "/" + "home" + "/bob/x"
WIN_HOME = "C:" + "\\" + "Users" + "\\" + "carol"
EMAIL = "alice" + AT + "example.net"
TOKENS = {
    "github-token": "gh" + "p_" + "a1B2c3D4e5F6g7H8i9J0k1L2",
    "github-pat": "github" + "_pat_" + "A1b2C3d4E5f6G7h8I9j0K1",
    "gitlab-token": "gl" + "pat-" + "abcdefghijklmnopqrst12",
    "slack-token": "xo" + "xb-" + "1234567890-abcdef",
    "aws-key": "AK" + "IA" + "ABCDEFGHIJKLMNOP",
    "private-key": "-----" + "BEGIN RSA PRIVATE KEY-----",
    "url-userinfo": "https://" + "bob:s3cret" + AT + "example.net/repo.git",
}


def run_engine(*args, cwd=ROOT, env=None, stdin=None):
    e = dict(os.environ)
    e.setdefault("PYTHONPATH", str(ROOT))
    e["PYTHONPATH"] = str(ROOT)
    if env:
        e.update(env)
    return subprocess.run([sys.executable, "-m", "engine", *args], cwd=cwd, env=e,
                          capture_output=True, text=True, input=stdin)


def ids(text, deny=()):
    return {pid for _, pid, _ in leakcheck.scan_text(text, list(deny))}


# --------------------------------------------------------------- built-ins

@pytest.mark.parametrize("sample,pid", [
    (HOME, "builtin:home-path"), (LINUX_HOME, "builtin:home-path"), (WIN_HOME, "builtin:home-path-win"),
    (EMAIL, "builtin:email"), *[(v, f"builtin:{k}") for k, v in TOKENS.items()],
])
def test_builtin_hits(sample, pid):
    assert pid in ids(f"see {sample} here")


@pytest.mark.parametrize("sample", [
    "~/Library/Application Support/x",
    "the regex /" + "Users" + "/[^/\\s]+ in prose",
    "noreply" + AT + "anthropic.com",
    "123+bob" + AT + "users.noreply.github.com",
    "ssh://git" + AT + "github.com/org/repo.git",
    "https://user:token" + AT + "…",
    "gh" + "p_short",
    "AK" + "IA" + "short",
    "https://example.net/a/b",
])
def test_builtin_near_misses(sample):
    assert ids(sample) == set()


def test_near_miss_fixture_file_is_clean():
    text = (ROOT / "tests/fixtures/leaks/near-miss.txt").read_text()
    assert ids(text, leakcheck.parse_denylist("cs:Foo\nci:foo\n")) == set()


# --------------------------------------------------------------- denylist syntax

def test_cs_term():
    deny = leakcheck.parse_denylist("cs:Foo")
    assert ids("Foo 2.0", deny) == {"deny#1"}
    assert ids("foo", deny) == set()


def test_ci_term_word_boundary():
    deny = leakcheck.parse_denylist("ci:foo")
    assert ids("FOO bar", deny) == {"deny#1"}
    assert ids("food", deny) == set()


def test_plain_is_ci():
    deny = leakcheck.parse_denylist("# comment\n\nfoo")
    assert ids("a Foo b", deny) == {"deny#3"}


def test_re_term():
    deny = leakcheck.parse_denylist("re:Foo\\s+v?\\d")
    assert ids("Foo v3", deny) == {"deny#1"}
    assert ids("Foo bar", deny) == set()


def test_trailing_comment_stripped():
    deny = leakcheck.parse_denylist("ci:zorblax   # a private name")
    assert ids("the zorblax plan", deny) == {"deny#1"}


# --------------------------------------------------------------- CC BY-SA

CORPUS_TEXT = ("The verification gate requires that every artifact is traced back to its "
               "originating requirement before the release candidate is accepted by the team.\n")


def test_ccbysa_shingle(tmp_path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "skill.md").write_text(CORPUS_TEXT)
    corpus = leakcheck.build_corpus(corpus_dir)
    copied = "Intro.\nIt says every artifact is traced back to its originating requirement before the release candidate ships.\n"
    assert [h[1] for h in leakcheck.scan_shingles(copied, corpus)] == ["ccbysa:shingle"]
    own_words = "Our summary: the gate links artifacts to requirements before release.\n"
    assert leakcheck.scan_shingles(own_words, corpus) == []


def test_ccbysa_quote_markdown():
    cite = "cache:" + "agile-v/skills/x.md:3"
    hit = f'The method states "every artifact is traced back first" ({cite}).\n'
    assert [h[1] for h in leakcheck.scan_quotes(hit, False)] == ["ccbysa:quote"]
    short = f'The method names a "trace gate" ({cite}).\n'
    assert leakcheck.scan_quotes(short, False) == []
    other = 'It says "every artifact is traced back first" (cache:bmad/x.md:1).\n'
    assert leakcheck.scan_quotes(other, False) == []


def test_ccbysa_quote_blockquote():
    cite = "cache:" + "agile-v/skills/x.md:3"
    text = f"Source {cite}:\n> every artifact is traced back to a requirement\n"
    assert [h[1] for h in leakcheck.scan_quotes(text, False)] == ["ccbysa:quote"]


def test_ccbysa_quote_json():
    cite = "cache:" + "agile-v/skills/x.md:3"
    hit = '{\n  "evidence": "' + cite + ' says \\"every artifact is traced back first\\""\n}\n'
    assert [h[1] for h in leakcheck.scan_quotes(hit, True)] == ["ccbysa:quote"]
    plain = '{\n  "evidence": "' + cite + ' shows a gate that runs before every release"\n}\n'
    assert leakcheck.scan_quotes(plain, True) == []


def test_ccbysa_missing_corpus_is_not_a_pass(tmp_path):
    (tmp_path / "a.md").write_text("clean\n")
    r = run_engine("leakcheck", "--path", str(tmp_path / "a.md"), "--ccbysa",
                   "--ccbysa-corpus", str(tmp_path / "absent"))
    assert r.returncode == 3


# --------------------------------------------------------------- CLI, hygiene

def test_cli_path_exit_codes(tmp_path):
    (tmp_path / "clean.md").write_text("nothing here\n")
    (tmp_path / "dirty.md").write_text(f"path {HOME}\n")
    assert run_engine("leakcheck", "--path", str(tmp_path / "clean.md")).returncode == 0
    r = run_engine("leakcheck", "--path", str(tmp_path / "dirty.md"))
    assert r.returncode == 5
    assert "builtin:home-path" in r.stdout


def test_ci_output_hygiene(tmp_path):
    terms = ["Quuxinator", "zebulon-prime"]
    deny = tmp_path / "deny.txt"
    deny.write_text("cs:Quuxinator\nre:zebu[l]on-pri(me)\n")
    target = tmp_path / "doc.md"
    target.write_text("We used Quuxinator here.\nAnd zebulon-prime there.\n")
    r = run_engine("leakcheck", "--path", str(target), "--denylist", str(deny), "--ci", "--show",
                   env={"CI": "true"})
    assert r.returncode == 5
    out = r.stdout + r.stderr
    for t in terms + ["zebu[l]on-pri(me)", "We used", "there."]:
        assert t not in out
    assert "deny#1" in out and "deny#2" in out


def test_matching_path_name_is_hashed(tmp_path):
    deny = tmp_path / "deny.txt"
    deny.write_text("ci:quuxinator\n")
    d = tmp_path / "scan"
    d.mkdir()
    (d / "quuxinator-notes.md").write_text("clean\n")
    r = run_engine("leakcheck", "--path", str(d), "--denylist", str(deny), "--ci")
    assert r.returncode == 5
    assert "quuxinator" not in (r.stdout + r.stderr).lower()
    assert "path#" in r.stdout


# --------------------------------------------------------------- git modes

def git(repo, *a):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t" + AT + "example.net",
                    "-c", "commit.gpgsign=false", *a], cwd=repo, check=True, capture_output=True)


def make_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    return path


def test_git_history_finds_deleted_file(tmp_path):
    repo = make_repo(tmp_path / "repo")
    (repo / "old.md").write_text("the zorblax plan\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "first")
    git(repo, "rm", "-q", "old.md")
    (repo / "new.md").write_text("clean\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "second")
    deny = tmp_path / "deny.txt"
    deny.write_text("ci:zorblax\n")
    assert run_engine("leakcheck", "--path", str(repo), "--denylist", str(deny), cwd=repo).returncode == 0
    r = run_engine("leakcheck", "--git-history", "--denylist", str(deny), cwd=repo)
    assert r.returncode == 5
    assert "old.md" in r.stdout


def test_git_history_scans_commit_messages(tmp_path):
    repo = make_repo(tmp_path / "repo")
    (repo / "a.md").write_text("clean\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "port the zorblax data")
    deny = tmp_path / "deny.txt"
    deny.write_text("ci:zorblax\n")
    r = run_engine("leakcheck", "--git-history", "--denylist", str(deny), cwd=repo)
    assert r.returncode == 5
    assert ":message:" in r.stdout


def test_staged_and_unpushed_scans_index(tmp_path):
    repo = make_repo(tmp_path / "repo")
    (repo / "a.md").write_text("clean\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "c1")
    (repo / "b.md").write_text(f"{EMAIL}\n")
    git(repo, "add", "-A")
    r = run_engine("leakcheck", "--staged-and-unpushed", cwd=repo)
    assert r.returncode == 5
    assert "index:b.md" in r.stdout


def test_licence_files_excluded_from_corpus(tmp_path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "LICENSE").write_text(CORPUS_TEXT)
    assert leakcheck.build_corpus(corpus_dir) == set()
