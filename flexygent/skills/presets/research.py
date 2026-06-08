from flexygent.skills import Skill

research_skill = Skill(
    name="research",
    description="Deep research — gather, synthesize, and analyze information from multiple sources to produce comprehensive insights.",
    identity_intro=(
        "You are also a thorough research analyst. "
        "You gather information from multiple sources, cross-reference facts, "
        "and synthesize findings into clear, well-structured summaries. "
        "You are objective, cite sources when possible, and distinguish "
        "between established knowledge and speculation. "
        "You use data analysis to validate or challenge assumptions."
    ),
    doc_path="skills/docs/research.md",
    allowed_tools=[
        "web_fetch",
        "read_file",
        "python_repl",
    ],
    config_overrides={
        "temperature": 0.8,
        "max_iterations": 15,
    },
)
