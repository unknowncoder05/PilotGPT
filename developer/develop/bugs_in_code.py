from get_logger import logger

def bugs_in_code(
    content,
    node_type,
    name,
    code_edit_gpt,
    table_completion_gpt,
):
    prompt = f"""write the possible bugs of the following code, focus only on the {node_type} named {name}"""
    bugs = table_completion_gpt(
        prompt,
        max_tokens=-1,
        temperature=0,
        headers=["name", "description", "solution", "criticality"],
        verbose_headers=["bug name(make it descriptive)", "description", "solution", "criticality[Low,High]"],
        extra_requirements = ["check all the possible inputs and how it might cause unexpected behavior", "make sure the bugs make sense", "there might not be bugs so leave it empty if that is the case"],
        chunk_able=True
    )
    logger.debug(f'found bugs: {bugs}')
    solved_bugs = []
    for bug in bugs:
        if 'high' in bug.get('criticality', '').lower():
            continue
        solved_bugs.append(bug)
        instruction = f"""solve the bug {bug['name']} on the {node_type} named {name} using this solution: {bug['solution']}
don't remove any of the previously created resources or change their inputs or outputs
{node_type} {name}: {content}
"""
        content = code_edit_gpt(content, instruction, max_tokens=-1)
        logger.debug(f'bug {bug["name"]} solved: {content}')
    return content, solved_bugs
