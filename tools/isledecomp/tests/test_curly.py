# nyuk nyuk nyuk
import pytest
from isledecomp.parser.parser import CurlyManager
from isledecomp.parser.util import sanitize_code_line


@pytest.fixture(name="curly")
def fixture_curly():
    return CurlyManager()


def test_simple(curly):
    curly.read_line("namespace Test {")
    assert curly.get_prefix() == "Test"
    curly.read_line("}")
    assert curly.get_prefix() == ""


def test_oneliner(curly):
    curly.read_line("class LegoEntity;")
    assert curly.get_prefix() == ""


def test_ignore_comments(curly):
    curly.read_line("namespace Test {")
    curly.read_line("// }")
    assert curly.get_prefix() == "Test"


@pytest.mark.xfail(reason="todo: need a real lexer")
def test_ignore_multiline_comments(curly):
    curly.read_line("namespace Test {")
    curly.read_line("/*")
    curly.read_line("}")
    curly.read_line("*/")
    assert curly.get_prefix() == "Test"
    curly.read_line("}")
    assert curly.get_prefix() == ""


def test_nested(curly):
    curly.read_line("namespace Test {")
    curly.read_line("namespace Foo {")
    assert curly.get_prefix() == "Test::Foo"
    curly.read_line("}")
    assert curly.get_prefix() == "Test"


sanitize_cases = [
    ("", ""),
    ("   ", ""),
    ("{", "{"),
    ("// comments {", ""),
    ("{ // why comment here", "{"),
    ("/* comments */ {", "{"),
    ('"curly in a string {"', '""'),
    ('if (!strcmp("hello { there }", g_test)) {', 'if (!strcmp("", g_test)) {'),
    ("'{'", "''"),
    ("weird_function('\"', hello, '\"')", "weird_function('', hello, '')"),
]


@pytest.mark.parametrize("start, end", sanitize_cases)
def test_sanitize(start: str, end: str):
    assert sanitize_code_line(start) == end
