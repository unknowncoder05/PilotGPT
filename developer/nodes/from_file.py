import hashlib
from developer.nodes.from_file_cache import get_file_nodes_cache, save_file_nodes_cache
from get_logger import logger

def get_file_nodes(gpt, file_path, use_cache=True, splitter=';', headers=["type", "name", "inputs", "outputs", "parent class", "is parent", "short description"]):
    GET_NODES_PROMPT_FORMAT = """from this file write the base nodes (variables, functions, function call, classes, ...) that would need to be modified
- for fields that don't apply to the node type, left an empty space None
- separate list fields by commas ','
- for inputs and outputs use format 'name:type' if a list, add the type of it's items
- if the file contains no nodes, write 'NO NODES FOUND'
>>>
{file_content}
<<<
parent nodes: 
{headers}
"""
    # TODO: set individual node hash
    with open(file_path) as f:
        file_content = f.read()
        file_hash = hashlib.sha256(file_content.encode()).hexdigest()

    # load cache if exists
    if use_cache:
        cashed_nodes = get_file_nodes_cache(file_path, file_hash=file_hash)
        if type(cashed_nodes) is list:
            return cashed_nodes

    # raw get nodes
    base_lines = [x for x in file_content.split("\n") if x.lstrip() == x and x]
    top_nodes = len(base_lines)
    if top_nodes == 0:
        return []
    prompt = GET_NODES_PROMPT_FORMAT.format(
        file_content="\n".join(base_lines), headers=splitter.join(headers))
    result = gpt(prompt, max_tokens=-1,
                 temperature=0, stop=['parent nodes:', 'child nodes:'])
    logger.debug(f"{prompt}{result}")
    if 'NO NODES FOUND' in result:
        return []
    raw_nodes = result.split('\n')
    nodes = []
    for raw_node in raw_nodes:
        if raw_node:
            raw_columns = raw_node.split(splitter)
            if len(raw_columns) != len(headers):
                continue
            node = dict(zip(headers, raw_columns))
            nodes.append(node)


    # save cache
    if use_cache:
        save_file_nodes_cache(file_path, nodes=nodes, file_hash=file_hash)

    return nodes[:top_nodes]