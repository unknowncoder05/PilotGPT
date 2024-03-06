from utils.dict_to_csv import dict_to_csv
from get_logger import logger


def get_task_plan_steps(prompt, relevant_nodes, new_nodes, table_completion_gpt,
                        headers=['node','task_step_description',
                                 'dependencies'],
                        verbose_headers=['node name','step description',
                                         'dependent on resources'],
                        ):
    TASK_PLAN_STEPS = """generate the general required modifications a software developer should do on each resource in the resource table in order to complete the task: {prompt}"""
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
                "name": "resource",
                "data": nodes
            },
        ],
        extra_requirements={
            "Make sure to reuse code that already exists, inherit and import properly"
        }
    )
    logger.debug(f"plan nodes: {nodes}")
    # join response data to nodes
    node_names = [node.get('name', '') for node in nodes if 'name' in node]
    for raw_step in raw_steps:
        dependencies = [
            dependency
            for dependency in raw_step['dependencies'] if dependency in node_names
        ]
        for i, node in enumerate(nodes):
            raw_step['node'] == node['name']
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
