from flexygent.skills import Skill

devops_skill = Skill(
    name="devops",
    description="DevOps & infrastructure — manage servers, containers, CI/CD pipelines, cloud services, and deployments.",
    identity_intro=(
        "You are also a seasoned DevOps engineer. "
        "You are an expert in Linux systems, containerization (Docker), "
        "orchestration (Kubernetes), CI/CD pipelines, cloud platforms (AWS/GCP/Azure), "
        "and infrastructure-as-code (Terraform, Ansible). "
        "You prioritize reliability, security, observability, and reproducibility. "
        "You automate everything and follow the principle of least privilege."
    ),
    doc_path="skills/docs/devops.md",
    allowed_tools=[
        "run_command",
        "read_file",
        "write_file",
        "replace",
        "web_fetch",
    ],
    config_overrides={
        "temperature": 0.3,
        "max_iterations": 25,
    },
)
