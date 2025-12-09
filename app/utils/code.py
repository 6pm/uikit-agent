"""Code utilities functions"""


def clean_code_output(content: str) -> str:
    """
    Remove markdown wrapper (```tsx and ```) if the model added it anyway.
    """
    content = content.strip()

    # Remove starting ```tsx or ```typescript or just ```
    if content.startswith("```"):
        # Find the first newline and remove everything before it
        content = content.split("\n", 1)[1]

    # Remove trailing ```
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]

    return content.strip()
