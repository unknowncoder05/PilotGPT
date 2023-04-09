from utils.dict_to_csv import dict_to_csv
from get_logger import logger


def get_task_plan_steps(gpt, prompt, relevant_nodes, new_nodes):
    TASK_PLAN_STEPS = """steps to complete the task
task: {prompt}
relevant resources:
{nodes}

steps example format:
resource name | step description | dependent on resources
greater | add a username string input and then log it with a greater message; |
bulk_greater | receive many usernames and calls the greater function for each one of them | greater
main | add a call to the bulk_greater function with the names karl, leo and juliet | bulk_greater, greater

steps:
resource name | step description | dependent on resources
"""
    # TODO: handle nodes with same name

    # join nodes
    nodes = new_nodes.copy()
    for file in relevant_nodes:
        for relevant_node in relevant_nodes[file]:
            new_node = relevant_node.copy()
            new_node['file'] = file
            new_node['exists'] = True
            nodes.append(new_node)

    # render gpt prompt
    rendered_new_nodes = dict_to_csv(nodes, headers=[
                                     "name", "type", "inputs", "outputs", "parent class", "short description", "file"], delimiter='|')
    rendered_steps_prompt = TASK_PLAN_STEPS.format(
        prompt=prompt, nodes=rendered_new_nodes)
    raw_steps = gpt(rendered_steps_prompt,
                    max_tokens=-1)

    # join response data to nodes
    node_names = [node.get('name', '') for node in nodes if 'name' in node]
    for raw_step in raw_steps.split("\n"):
        try:
            raw_step_columns = raw_step.split("|")
            name, task_step_description, dependencies = [
                x.strip() for x in raw_step_columns]
            for i, node in enumerate(nodes):
                if node['name'] == name:
                    nodes[i]['task_step_description'] = task_step_description
                    nodes[i]['dependencies'] = [dependency.strip(
                    ) for dependency in dependencies if dependency.strip() in node_names]
                    yield nodes[i]
        except Exception as e:
            logger.error(f"get_task_plan_steps: {e}")
            logger.debug("rendered_steps_prompt:")
            logger.debug(rendered_steps_prompt+raw_step)


def log_task_steps(node_steps):
    logger.debug("# modifying")
    existing_nodes = [
        node_step for node_step in node_steps if node_step.get('exists')]
    if len(existing_nodes) > 0:
        logger.debug(dict_to_csv(existing_nodes, delimiter='\t'))
    else:
        logger.debug("-")

    logger.debug("# creating:")
    new_nodes = [
        node_step for node_step in node_steps if not node_step.get('exists')]
    if len(new_nodes) > 0:
        logger.debug(dict_to_csv(new_nodes, delimiter='\t'))
    else:
        logger.debug("-")
