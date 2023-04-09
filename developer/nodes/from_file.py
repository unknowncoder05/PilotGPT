import hashlib
from developer.nodes.from_file_cache import get_file_nodes_cache, save_file_nodes_cache
from get_logger import logger


def get_file_nodes(table_completion_gpt, file_path=None, file_content=None, use_cache=True, headers=["type", "name", "inputs", "outputs", "parent class", "is parent", "short description"]):
    # TODO: make sure file_path or file_content
    GET_NODES_PROMPT_FORMAT = """from this file write the base nodes (variables, functions, function call, classes, ...)
file content:
{file_content}"""
    if not file_content:
        # TODO: set individual node hash
        with open(file_path) as f:
            file_content = f.read()
            file_hash = hashlib.sha256(file_content.encode()).hexdigest()

        # load cache if exists
        if use_cache:
            cashed_nodes = get_file_nodes_cache(file_path, file_hash=file_hash)
            if type(cashed_nodes) is list:
                return cashed_nodes

    # TODO: this might have the unintended consequence of leaving behind a  class called like "Utils" with tons of functionality
    base_lines = [x for x in file_content.split("\n") if x.lstrip() == x and x]
    top_nodes = len(base_lines)
    if top_nodes == 0:
        return []
    prompt = GET_NODES_PROMPT_FORMAT.format(file_content=file_content)
    file_nodes = table_completion_gpt(
        prompt, max_tokens=-1,
        temperature=0,
        headers=headers,
        verbose_headers=["type", "name", "inputs", "outputs", "is parent[True,False]", "parent class(the class from which it inherits)", "short description"],
    )
    logger.debug(f"file_nodes: {file_nodes}")
    nodes = []
    for raw_node in file_nodes:
        if len(raw_node) != len(headers):
            continue
        nodes.append(raw_node)

    # save cache
    if not file_content and use_cache:
        save_file_nodes_cache(file_path, nodes=nodes, file_hash=file_hash)

    return nodes[:top_nodes]
