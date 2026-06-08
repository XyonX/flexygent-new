from flexygent.skills import Skill

coding_skill = Skill(
    name="coding",
    description="Expert software development — write, read, refactor, and debug code across any language or stack.",
    identity_intro=(
        "You are also a world-class software engineer. "
        "You write clean, well-documented, maintainable code. "
        "You follow language-specific best practices, use meaningful names, "
        "handle edge cases, and always consider performance and readability. "
        "When debugging, you reason step-by-step and use tools to verify your hypotheses."
    ),
    doc_path="skills/docs/coding.md",
    allowed_tools=[
        "read_file",
        "write_file",
        "replace",
        "python_repl",
        "run_command",
        "web_fetch",
    ],
    config_overrides={
        "max_iterations": 20,
        "temperature": 0.3,
    },
)
