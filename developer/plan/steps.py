from utils.dict_to_csv import dict_to_csv
from get_logger import logger


def get_task_plan_steps(prompt, relevant_nodes, new_nodes, table_completion_gpt,
                        headers=['task_step_description',
                                 'dependencies'],
                        verbose_headers=['step description',
                                         'dependent on resources'],
                        ):
    TASK_PLAN_STEPS = """generate the general required actions on each node in order to complete the task: {prompt}"""
    # TODO: handle nodes with same name

    # join nodes
    nodes = new_nodes.copy()
    for relevant_node in relevant_nodes:
        new_node = relevant_node.copy()
        new_node['exists'] = True
        nodes.append(new_node)
    # render gpt prompt
    rendered_steps_prompt = TASK_PLAN_STEPS.format(
        prompt=prompt)
    raw_steps = table_completion_gpt(
        rendered_steps_prompt,
        max_tokens=-1,
        temperature=0,
        headers=headers,
        verbose_headers=verbose_headers,
        context_tables=[
            {
                "name": "relevant resources",
                "data": nodes
            },
        ],
    )
    # join response data to nodes
    node_names = [node.get('name', '') for node in nodes if 'name' in node]
    for i, raw_step in enumerate(raw_steps):
        dependencies = [
            dependency
            for dependency in raw_step['dependencies'] if dependency in node_names
        ]
        nodes[i]['task_step_description'] = raw_step['task_step_description']
        nodes[i]['dependencies'] = dependencies
        yield nodes[i]
        break


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
