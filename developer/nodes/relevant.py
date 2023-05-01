from developer.nodes.from_file import get_file_nodes
from get_logger import logger


def get_relevant_nodes(prompt, selection_gpt, table_completion_gpt=None, relevant_files=[], nodes_by_file=None, minimum_node_relevance_rating=2):
    # TODO: make sure either relevant_files or nodes_by_file
    GET_RELEVANT_NODES_PROMPT_FORMAT = """find the relevant nodes (variables, functions, function call, classes, ...) that would need to be modified or linked for the task: {task}"""
    if not nodes_by_file:
        # TODO: make nodes_by_file an iterable
        # TODO: validate table_completion_gpt is set if not nodes_by_file
        nodes_by_file = [(file_name, get_file_nodes(table_completion_gpt, file_name)) for file_name in relevant_files]
    relevant_nodes = []
    for file_name, file_nodes in nodes_by_file:
        # TODO: optimize node file names
        if not file_nodes:
            continue
        relevant_nodes_prompt = GET_RELEVANT_NODES_PROMPT_FORMAT.format(
            task=prompt)
        raw_relevant_nodes = selection_gpt(
            relevant_nodes_prompt, max_tokens=-1,
            options_table=file_nodes,
            temperature=0,
            headers=["name", "node_type", "inputs", "outputs", "parent class", "is parent", "short description"],
            rating = [0,10],
            rating_threshold = 2,
            chunk_able=True,
        )
        logger.debug(f"raw_relevant_nodes: {raw_relevant_nodes}")
        # set file to all new nodes
        for i in range(len(raw_relevant_nodes)):
            raw_relevant_nodes[i]['file'] = file_name
        relevant_nodes.extend(raw_relevant_nodes)

    return relevant_nodes
