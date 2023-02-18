TASK_CLARIFICATIONS = """for the implementation of this feature, the possible previous clarifications required before starting would be, (give a high, medium, low rating depending on if it is critical before starting, follow the format "<rating>: <description>"):
feature:
{prompt}
clarifications:
"""

def get_task_clarifications(gpt, prompt):
    return gpt(TASK_CLARIFICATIONS.format(prompt=prompt), max_tokens=1000)
