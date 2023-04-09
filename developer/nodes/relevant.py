from developer.nodes.from_file import get_file_nodes
from get_logger import logger


def get_relevant_nodes(gpt, prompt, relevant_files, headers=["type", "name", "inputs", "outputs", "parent class", "is parent", "short description"]):
    GET_RELEVANT_NODES_PROMPT_FORMAT = """find the relevant related node names for the task
task:
{task}
existing nodes:
{nodes}
example result:
- node name, relevance rating[0,10]
related node names:
-"""
    nodes_by_file = {}
    for file_name in relevant_files:
        file_nodes = get_file_nodes(gpt, file_name)
        if not file_nodes:
            continue
        rendered_nodes = '\t'.join(headers)
        if not file_nodes:
            continue
        for node in file_nodes:
            rendered_nodes += '\n'
            rendered_nodes += '\t'.join(node.values())
        relevant_nodes_prompt = GET_RELEVANT_NODES_PROMPT_FORMAT.format(
            task=prompt, nodes=rendered_nodes)
        response = gpt(relevant_nodes_prompt, max_tokens=-1,
                       temperature=0)
        try:
            relevant_node_names = list()
            for relevant_node in response.split('\n-'):
                node_name, relevance_rating = relevant_node.split(",")
                if int(relevance_rating) > 2:
                    relevant_node_names.append(node_name.strip())
            nodes_by_file[file_name] = [
                node for node in file_nodes if 'name' in node and node['name'] in relevant_node_names]
        except Exception as e:
            logger.error(e)
            logger.debug(relevant_node)

    return nodes_by_file
