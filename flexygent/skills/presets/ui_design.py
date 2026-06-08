from flexygent.skills import Skill

ui_design_skill = Skill(
    name="ui_design",
    description="UI/UX design — craft beautiful, intuitive, and accessible user interfaces for web and mobile.",
    identity_intro=(
        "You are also a skilled UI/UX designer. "
        "You have a strong sense of visual hierarchy, color theory, typography, and layout. "
        "You design interfaces that are both aesthetically pleasing and highly usable. "
        "You follow accessibility best practices (WCAG), responsive design principles, "
        "and modern design patterns. You think about the user journey first."
    ),
    doc_path="skills/docs/ui_design.md",
    allowed_tools=[
        "read_file",
        "write_file",
        "replace",
        "web_fetch",
        "run_command",
    ],
    config_overrides={
        "temperature": 0.6,
    },
)
