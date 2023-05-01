from developer.files.relevant import get_relevant_files
from developer.nodes.relevant import get_relevant_nodes
from developer.plan.steps import get_task_plan_steps, log_task_steps
from developer.nodes.new_nodes import get_new_nodes
from get_logger import logger


def get_task_plan(table_completion_gpt, selection_gpt, prompt, target_dir, relevant_files=None, relevant_nodes=None, new_nodes=None, exclude_files=None, rexclude_files=None):
    # Relevant files
    if not relevant_files:
        relevant_files = get_relevant_files(
            table_completion_gpt, prompt, target_dir, exclude_files=exclude_files, rexclude_files=rexclude_files)
    logger.debug(f"relevant_files: {relevant_files}")

    # Relevant nodes in files
    if not relevant_nodes:
        relevant_nodes = get_relevant_nodes(prompt=prompt, selection_gpt=selection_gpt, table_completion_gpt=table_completion_gpt, relevant_files=relevant_files)
    logger.debug(f"relevant_nodes: {relevant_nodes}")

    # New nodes
    if not new_nodes:
        new_nodes = get_new_nodes(
            prompt=prompt, nodes=relevant_nodes, table_completion_gpt=table_completion_gpt, relevant_files_and_folders=relevant_files)
    logger.debug(f"new_nodes: {new_nodes}")
    steps = get_task_plan_steps(prompt, relevant_nodes, new_nodes, table_completion_gpt=table_completion_gpt)
    steps = list(steps)

    log_task_steps(steps)
    return steps
