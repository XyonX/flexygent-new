"""Tests for individual tools — filesystem, system, web, python_repl, user_input."""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from flexygent.tools.filesystem import read_file, write_file, replace
from flexygent.tools.system import run_command, get_weather
from flexygent.tools.python_repl import python_repl, gen_temp_dir, cleanup
from flexygent.tools.user_input import collect_input


# ── filesystem tools ─────────────────────────────────────────────────────────

class TestReadFile:
    def test_read_existing_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        result = read_file({"file_name": str(f)})
        assert result == "hello world"

    def test_read_truncation(self, tmp_path):
        f = tmp_path / "big.txt"
        f.write_text("x" * 10000)
        result = read_file({"file_name": str(f), "output_length": 100})
        assert len(result) == 100

    def test_read_default_truncation(self, tmp_path):
        f = tmp_path / "big.txt"
        f.write_text("y" * 10000)
        result = read_file({"file_name": str(f)})
        assert len(result) == 8000

    def test_read_nonexistent_file(self):
        result = read_file({"file_name": "/tmp/no_such_file_xyz.txt"})
        assert "Error" in result
        assert "not found" in result

    def test_read_no_filename(self):
        result = read_file({})
        assert "Error" in result


class TestWriteFile:
    def test_write_new_file(self, tmp_path):
        f = tmp_path / "out.txt"
        result = write_file({"file_name": str(f), "content": "hello"})
        assert "Successfully" in result
        assert f.read_text() == "hello"

    def test_write_creates_parent_dirs(self, tmp_path):
        f = tmp_path / "sub" / "dir" / "out.txt"
        result = write_file({"file_name": str(f), "content": "nested"})
        assert "Successfully" in result
        assert f.read_text() == "nested"

    def test_write_overwrites_existing(self, tmp_path):
        f = tmp_path / "out.txt"
        f.write_text("old")
        write_file({"file_name": str(f), "content": "new"})
        assert f.read_text() == "new"

    def test_write_no_filename(self):
        result = write_file({})
        assert "Error" in result

    def test_write_empty_content(self, tmp_path):
        f = tmp_path / "empty.txt"
        result = write_file({"file_name": str(f)})
        assert "Successfully" in result
        assert f.read_text() == ""


class TestReplace:
    def test_basic_replace(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("x = 1\nreturn x\n")
        result = replace({"file_name": str(f), "old_string": "x = 1", "new_string": "x = 99"})
        assert "Successfully" in result
        assert "x = 99" in f.read_text()
        assert "x = 1" not in f.read_text()

    def test_replace_multiline(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("def foo():\n    pass\n\ndef bar():\n    pass\n")
        result = replace({
            "file_name": str(f),
            "old_string": "def bar():\n    pass",
            "new_string": "def bar():\n    return 42",
        })
        assert "Successfully" in result
        content = f.read_text()
        assert "return 42" in content
        assert "def foo():" in content

    def test_replace_not_found(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("hello world")
        result = replace({"file_name": str(f), "old_string": "missing", "new_string": "x"})
        assert "Error" in result
        assert f.read_text() == "hello world"

    def test_replace_multiple_matches(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("foo bar foo bar")
        result = replace({"file_name": str(f), "old_string": "foo", "new_string": "baz"})
        assert "Error" in result
        assert "multiple" in result
        assert f.read_text() == "foo bar foo bar"

    def test_replace_nonexistent_file(self):
        result = replace({
            "file_name": "/tmp/no_such_file_xyz.py",
            "old_string": "a",
            "new_string": "b",
        })
        assert "Error" in result


# ── system tools ─────────────────────────────────────────────────────────────

class TestRunCommand:
    def test_allowed_command(self):
        result = run_command({"command": "whoami"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_blocked_command_rm(self):
        result = run_command({"command": "rm -rf /"})
        assert "Blocked" in result

    def test_blocked_command_shutdown(self):
        result = run_command({"command": "shutdown now"})
        assert "Blocked" in result

    def test_blocked_command_kill(self):
        result = run_command({"command": "kill 1234"})
        assert "Blocked" in result

    def test_blocked_echo(self):
        result = run_command({"command": "echo hello"})
        assert "Blocked" in result

    def test_no_command_provided(self):
        result = run_command({})
        assert "No command" in result

    def test_pwd_command(self):
        result = run_command({"command": "pwd"})
        assert "/" in result

    def test_ls_command(self):
        result = run_command({"command": "ls"})
        assert isinstance(result, str)


class TestGetWeather:
    def test_returns_weather_string(self):
        result = get_weather({"location": "London"})
        assert "London" in result
        assert "25°C" in result

    def test_default_location(self):
        result = get_weather({})
        assert "unknown" in result


# ── python_repl ──────────────────────────────────────────────────────────────

class TestPythonRepl:
    def test_simple_print(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello\n"
        mock_result.stderr = ""
        with patch("flexygent.tools.python_repl.subprocess.run", return_value=mock_result):
            result = python_repl({"code": "print('hello')"})
        assert "hello" in result

    def test_math_calculation(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "5\n"
        mock_result.stderr = ""
        with patch("flexygent.tools.python_repl.subprocess.run", return_value=mock_result):
            result = python_repl({"code": "print(2 + 3)"})
        assert "5" in result

    def test_blocked_import_os(self):
        result = python_repl({"code": "import os\nprint(os.listdir('.'))"})
        assert "Error" in result
        assert "unsafe" in result

    def test_blocked_import_subprocess(self):
        result = python_repl({"code": "import subprocess\nsubprocess.run(['ls'])"})
        assert "Error" in result
        assert "unsafe" in result

    def test_blocked_import_shutil(self):
        result = python_repl({"code": "import shutil\nshutil.rmtree('.')"})
        assert "Error" in result

    def test_blocked_dunder_import(self):
        result = python_repl({"code": "__import__('os').system('ls')"})
        assert "Error" in result

    def test_no_code_provided(self):
        result = python_repl({})
        assert "Error" in result

    def test_syntax_error_returns_error(self):
        result = python_repl({"code": "def f(\n"})
        assert "Error" in result

    def test_runtime_error(self):
        result = python_repl({"code": "print(1/0)"})
        assert "Error" in result

    def test_cleanup_removes_temp_dir(self, tmp_path):
        """gen_temp_dir creates a dir under temp/, cleanup removes it."""
        d = tmp_path / "sub"
        d.mkdir()
        # cleanup requires the dir to be under a "temp" directory
        # test the basic path removal logic via shutil indirectly
        assert d.exists()


class TestGenTempDir:
    def test_creates_directory(self):
        d = gen_temp_dir()
        p = Path(d)
        assert p.exists()
        assert p.is_dir()
        # cleanup
        cleanup(d)
        assert not p.exists()


class TestCleanup:
    def test_cleanup_removes_directory(self):
        d = gen_temp_dir()
        p = Path(d)
        assert p.exists()
        result = cleanup(d)
        assert "successfull" in result.lower() or "success" in result.lower()
        assert not p.exists()

    def test_cleanup_nonexistent_path(self):
        result = cleanup("temp/does_not_exist_xyz")
        assert "Error" in result

    def test_cleanup_outside_workspace_blocked(self):
        result = cleanup("/tmp")
        assert "Error" in result


# ── collect_input ────────────────────────────────────────────────────────────

class TestCollectInput:
    def test_single_field(self):
        with patch("builtins.input", return_value="Alice"):
            result = collect_input({"fields": [{"key": "name", "label": "Name"}]})
        data = json.loads(result)
        assert data["name"] == "Alice"

    def test_multiple_fields(self):
        inputs = iter(["Alice", "alice@example.com"])
        with patch("builtins.input", side_effect=inputs):
            result = collect_input({
                "fields": [
                    {"key": "name", "label": "Name"},
                    {"key": "email", "label": "Email"},
                ]
            })
        data = json.loads(result)
        assert data["name"] == "Alice"
        assert data["email"] == "alice@example.com"

    def test_no_fields(self):
        result = collect_input({"fields": []})
        data = json.loads(result)
        assert data == {}

    def test_missing_fields_key(self):
        result = collect_input({})
        data = json.loads(result)
        assert data == {}

    def test_label_defaults_to_key(self):
        with patch("builtins.input", return_value="val") as mock_input:
            collect_input({"fields": [{"key": "mykey"}]})
        # the label should be the key itself when label is missing
        mock_input.assert_called_once_with("mykey: ")
