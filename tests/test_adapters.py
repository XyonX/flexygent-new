"""Tests for flexygent.interfaces and flexygent.adapters.cli."""

import pytest
from unittest.mock import patch
from flexygent.interfaces import UserIO
from flexygent.adapters.cli import CliUserIO


# ── UserIO ABC ───────────────────────────────────────────────────────────────

class TestUserIOABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            UserIO()

    def test_subclass_must_implement_get_input(self):
        class Partial(UserIO):
            def show_output(self, message):
                pass
            # missing get_input

        with pytest.raises(TypeError):
            Partial()

    def test_subclass_must_implement_show_output(self):
        class Partial(UserIO):
            def get_input(self, prompt=""):
                pass
            # missing show_output

        with pytest.raises(TypeError):
            Partial()

    def test_valid_subclass_instantiates(self):
        class Complete(UserIO):
            def get_input(self, prompt=""):
                return "test"
            def show_output(self, message):
                pass

        io = Complete()
        assert io.get_input() == "test"


# ── CliUserIO ────────────────────────────────────────────────────────────────

class TestCliUserIO:
    def test_is_instance_of_userio(self):
        io = CliUserIO()
        assert isinstance(io, UserIO)

    def test_get_input_calls_builtin_input(self):
        io = CliUserIO()
        with patch("builtins.input", return_value="hello") as mock_input:
            result = io.get_input("Enter: ")
        mock_input.assert_called_once_with("Enter: ")
        assert result == "hello"

    def test_show_output_calls_print(self, capsys):
        io = CliUserIO()
        io.show_output("test message")
        captured = capsys.readouterr()
        assert "test message" in captured.out

    def test_get_input_empty_prompt(self):
        io = CliUserIO()
        with patch("builtins.input", return_value="value") as mock_input:
            result = io.get_input("")
        mock_input.assert_called_once_with("")
        assert result == "value"
