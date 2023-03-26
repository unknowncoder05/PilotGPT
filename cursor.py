import csv
from io import StringIO
import ast
import re
import openai
import os
import json
from utils.node_description import tree_node_names
import hashlib

INFO = True


def check_content_filter(prompt):
    if INFO:
        print('gpt call')
    completions = openai.Completion.create(
        engine="content-filter-alpha",
        prompt=prompt,
        max_tokens=1,
        temperature=0,
        top_p=0
    )
    return completions.choices[0].text


def execute_completion_model(prompt, model="code-davinci-002", temperature=0, max_tokens=100, many=False, *args, **kwargs):
    """
    Executes the completion model with the given parameters and returns the list of responses.
    """
    if INFO:
        print('gpt call')
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        *args, **kwargs
    )
    if many:
        return [x.text.strip() for x in response.choices]
    else:
        return response.choices[0].text.strip()


def execute_code_edit_model(input, instruction, model="code-davinci-edit-001", temperature=0, max_tokens=100, many=False, *args, **kwargs):
    """
    Executes the completion model with the given parameters and returns the list of responses.
    """
    if INFO:
        print('gpt call')
    response = openai.Edit.create(
        model=model,
        input=input,
        temperature=temperature,
        instruction=instruction,
        *args, **kwargs
    )
    if many:
        return [x.text.strip() for x in response.choices]
    else:
        return response.choices[0].text.strip()


def open_ai_model_func(model, type='completion'):
    """
    Returns a function that executes the given model with the specified type.
    """
    if type == 'completion':
        def execute(prompt_text, *args, **kwargs):
            return execute_completion_model(prompt_text, model=model, *args, **kwargs)
        return execute
    if type == 'code_edit':
        def execute(prompt_text, instruction, *args, **kwargs):
            return execute_code_edit_model(prompt_text, instruction, model=model, *args, **kwargs)
        return execute

# utils


def list_py_files(dir_path: str, exclude_files=[], rexclude_files=[]):
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if not file.endswith('.py'):
                continue
            file_path = os.path.join(root, file)
            is_valid = True
            for rexclude_file in rexclude_files:  # TODO: make it .gitignore style
                if rexclude_file in file_path:
                    is_valid = False
                    break
            if not is_valid:
                continue

            yield file_path


def is_included_file(file_path, exclude_files=[], rexclude_files=[]):
    for rexclude_file in rexclude_files:  # TODO: make it .gitignore style
        if rexclude_file in file_path:
            return False
    return True


def list_files_recursively(dir_path: str, exclude_files=[], rexclude_files=[]):
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            is_valid = True
            for rexclude_file in rexclude_files:  # TODO: make it .gitignore style
                if rexclude_file in file_path:
                    is_valid = False
                    break
            if not is_valid:
                continue
            yield file_path


def list_directories_recursively(path, exclude_files=[], rexclude_files=[]):
    directories = []
    # Get the names of the items in the directory
    items = os.listdir(path)
    for item in items:
        # Build the full path of the item
        item_path = os.path.join(path, item)
        # Check if the item is a directory
        if os.path.isdir(item_path):
            # filter
            is_valid = True
            for rexclude_file in rexclude_files:  # TODO: make it .gitignore style
                if rexclude_file in item_path:
                    is_valid = False
                    break
            if not is_valid:
                continue
            # Add the directory to the list
            directories.append(item_path)
            # Recursively list the directories in the subdirectory
            directories += list_directories_recursively(
                item_path, exclude_files=exclude_files, rexclude_files=rexclude_files)
    return directories


def list_directory_items(path, exclude_files=[], rexclude_files=[]):
    # Get the names of the items in the directory
    items = os.listdir(path)

    # Create a list of objects containing the type and name of each item
    item_list = []
    for item in items:
        item_path = os.path.join(path, item)
        if not is_included_file(item_path, exclude_files=exclude_files, rexclude_files=rexclude_files):
            continue
        if os.path.isdir(item_path):
            item_type = "d"
        else:
            item_type = "f"
        item_list.append({"type": item_type, "name": item})
    return item_list


def list_file_nodes(files, target_dir) -> dict:
    file_descriptions = dict()
    for file_name in files:
        node_names = '\n'.join(tree_node_names(file_name))
        tokens = len(node_names) / TOKENS_TO_CHARACTERS
        if tokens > RECOMMENDED_TOKENS_PER_FILE:
            print(
                f"Warning, this file has {tokens:.2f} tokens and may cause an overflow in the input size, make sure to decouple ")
        file_descriptions[file_name.replace(target_dir, '')] = node_names
    total_tokens = sum([len(node_names)
                       for node_names in file_descriptions.values()]) / TOKENS_TO_CHARACTERS
    if total_tokens > MAX_TOKENS:
        print(
            f"Warning, this project is big and may cause an overflow in the input size, make sure to decouple {total_tokens:.2f}")
    return file_descriptions


TASK_CLARIFICATIONS = """for the implementation of this feature, the possible previous clarifications required before starting would be, (give a high, medium, low rating depending on if it is critical before starting, follow the format "<rating>: <description>"):
feature:
{prompt}
clarifications:
"""

TASK_PLAN = """for the following task, for each file write what code is needed to develop it, follow the following rules:
- use the step format
- if needed add more than one action per file
- follow the already existing structure of the project when possible
- if needed create new files by just adding win the action field what should be it's content, write "empty" if there is no need to add content
- don't modify files which don't need to be modified
- focus only on the task at hand
- follow the pep-8 rules 
step format:
{{
    "file": "./file",
    "action": "action to be done",
    "results": [{{"name": "expected name of created item", "type": "class/variable/function/etc", "inputs": [], "outputs": []}}]
 }}
task:
{prompt}
directories:
{all_directories}
files:
{files}
json plan: [
"""

# {{"filename": "...", "actions":["actions to be done in this file"]}}
PROMPT_PLAN = """to develop the following feature move through the repository and check which files need to be modified
- write "ls <directory>" to list the items in a directory
- write "content <file>" to check the relevant information of a python file
- write "done <list>" with a list of json objects like ["relevant_file"] when all the relevant information to generate a plan is gathered
- avoid repeating commands
- avoid executing unnecessary commands
- make sure to first find all relevant files
feature: {prompt}
exploration:
in: ls ./
out: {initial_files}"""

openai.api_key = os.getenv("OPENAPI_API_KEY")
gpt = open_ai_model_func("text-davinci-002")
code_edit_gpt = open_ai_model_func("code-davinci-edit-001", type="code_edit")

TOKENS_TO_CHARACTERS = 0.75
MAX_TOKENS = 4097
RECOMMENDED_TOKENS_PER_FILE = 3000


def file_description(file_name):
    if file_name.endswith(".py"):
        return tree_node_names(file_name)
    else:
        return "not a python file"

# ask the ai to explore a project and decide which files a re relevant


def iterative_planning(prompt, target_dir, debug=False, manual=False, input_field="in:", output_field="out:", exclude_files=[], rexclude_files=[], max_iterations=20):
    initial_files = list_directory_items(
        target_dir, exclude_files=exclude_files, rexclude_files=rexclude_files)
    plan_prompt = PROMPT_PLAN.format(
        prompt=prompt, initial_files=initial_files) + "\n"+input_field
    last_iteration = 0
    plan = ""
    for i in range(max_iterations):
        if manual and input("continue? y/N: ") != "y":
            print("manual exit")
            break
        last_iteration = i
        # print(plan_prompt)
        try:
            response = gpt(plan_prompt, max_tokens=1000,
                           temperature=0, stop=['\n'])
        except Exception as e:
            print(e)
            return last_iteration, plan_prompt, plan
        action_result = ""
        if debug:
            print(last_iteration, input_field, response)
        if response.startswith("ls"):
            file_name = target_dir+"/"+response.split(" ")[1].replace("./", "")
            if os.path.exists(file_name):
                files = list_directory_items(
                    file_name, exclude_files=exclude_files, rexclude_files=rexclude_files)
                action_result = str(files)
            else:
                action_result = "not such file"
        elif response.startswith("content"):
            file_name = target_dir+"/"+response.split(" ")[1].replace("./", "")
            if os.path.exists(file_name):
                files = file_description(file_name)
                action_result = ">>>\n"+str(files)+"\n<<<"
            else:
                action_result = "not such file"
        elif response.startswith("done"):
            print("successful exit")
            plan = response
            break
        plan_prompt += response + "\n" + output_field + action_result + "\n"+input_field
        if debug:
            print(output_field, action_result)
    return last_iteration, plan_prompt, plan


def slice_list_by_tokens(items, tokens_to_characters=TOKENS_TO_CHARACTERS, max_tokens=MAX_TOKENS):
    current_list = []
    current_token_count = 0
    for item in items:
        item_token_count = len(item) / tokens_to_characters
        current_list.append(item)
        current_token_count += item_token_count

        if current_token_count > max_tokens:
            yield current_list
            current_list = []
            current_token_count = 0
    if current_list:
        yield current_list


def get_relevant_files(prompt, target_dir, exclude_files=[], rexclude_files=[]):
    RELEVANT_DIRECTORIES = """to develop the following feature which files need to be modified
- keep in mind this are not all the available files so if no relevant file is found, return "None"
- list all related files that would need to be modified or that may contain needed resources
feature: {prompt}
files:
{files}
example result;
- file name, relevance rating[0,10]
result:
-"""
    files_generator = list_files_recursively(
        target_dir, exclude_files=exclude_files, rexclude_files=rexclude_files)
    initial_tokens = (len(RELEVANT_DIRECTORIES) +
                      len(prompt)) / TOKENS_TO_CHARACTERS
    expected_tokens = MAX_TOKENS-initial_tokens

    relevant_directories = []
    calls = 0
    for chunk_of_files in slice_list_by_tokens(files_generator, max_tokens=expected_tokens):
        calls += 1
        relevant_files_prompt = RELEVANT_DIRECTORIES.format(
            prompt=prompt, files="\n".join([x.replace(target_dir+"/", "") for x in chunk_of_files]))
        response = gpt(relevant_files_prompt, max_tokens=MAX_TOKENS - len(relevant_files_prompt),
                       temperature=0)
        if response and "None" not in response:
            # TODO: proper cleaning
            for file_response in response.split("\n-"):
                file_name, relevance_value = file_response.split(',')
                file_name = target_dir+'/'+file_name.strip().replace('./', '')
                if int(relevance_value) > 2:
                    relevant_directories.append(file_name)
    return relevant_directories, calls


def get_file_nodes(file_path, use_cache=True, splitter=';', headers=["type", "name", "inputs", "outputs", "parent class", "is parent", "short description"]):
    GET_NODES_PROMPT_FORMAT = """from this file write the base nodes (variables, functions, function call, classes, ...) that would need to be modified
- for fields that don't apply to the node type, left an empty space None
- separate list fields by commas ','
- for inputs and outputs use format 'name:type' if a list, add the type of it's items
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
    prompt = GET_NODES_PROMPT_FORMAT.format(
        file_content="\n".join(base_lines), headers=splitter.join(headers))
    result = gpt(prompt, max_tokens=MAX_TOKENS - len(prompt),
                 temperature=0, stop=['parent nodes:', 'child nodes:'])
    nodes = [dict(zip(headers, x.split(splitter))) for x in result.split('\n')]

    # save cache
    if use_cache:
        save_file_nodes_cache(file_path, nodes=nodes, file_hash=file_hash)

    return nodes


def get_file_nodes_cache(file_path, file_hash=None, cache_directory='pilot.cache'):
    # TODO: use path.join
    current_cache_directory = os.path.dirname(
        file_path) + "/" + cache_directory
    current_cache_file = current_cache_directory + \
        "/"+os.path.basename(file_path)+".json"

    if not os.path.exists(current_cache_file):
        return None

    try:
        with open(current_cache_file, 'r') as f:
            cache = json.load(f)

        if not file_hash:
            with open(file_path, 'r') as f:
                file_content = f.read()
                file_hash = hashlib.sha256(file_content.encode()).hexdigest()
        if cache.get('file_hash') != file_hash:
            return None

        return cache.get('nodes')
    except Exception as e:
        print("CACHE ERROR", e)
        return None


def save_file_nodes_cache(file_path, nodes, file_hash=None, cache_directory='pilot.cache'):
    # TODO: use path.join
    current_cache_directory = os.path.dirname(
        file_path) + "/" + cache_directory
    current_cache_file = current_cache_directory + \
        "/"+os.path.basename(file_path) + ".json"

    if not os.path.exists(current_cache_directory):
        os.makedirs(current_cache_directory, exist_ok=True)

    if not file_hash:
        with open(file_path, 'r') as f:
            file_content = f.read()
            file_hash = hashlib.sha256(file_content.encode()).hexdigest()

    with open(current_cache_file, 'w') as f:
        json.dump(dict(nodes=nodes, file_hash=file_hash), f, indent=4)


def get_relevant_nodes(prompt, relevant_files, headers=["type", "name", "inputs", "outputs", "parent class", "is parent", "short description"]):
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
        file_nodes = get_file_nodes(file_name)
        if not file_nodes:
            continue
        rendered_nodes = '\t'.join(headers)
        for node in file_nodes:
            rendered_nodes += '\n'
            rendered_nodes += '\t'.join(node.values())
        relevant_nodes_prompt = GET_RELEVANT_NODES_PROMPT_FORMAT.format(
            task=prompt, nodes=rendered_nodes)
        response = gpt(relevant_nodes_prompt, max_tokens=MAX_TOKENS - len(relevant_nodes_prompt),
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
            print('ERROR get_relevant_nodes', e)

    return nodes_by_file


def render_nodes_table(nodes_by_file, headers=["type", "name", "inputs", "outputs", "parent class", "is parent", "short description", "file"]):
    rendered_node_headers = ';'.join(headers)
    rendered_nodes_table = rendered_node_headers
    for file in nodes_by_file:
        for node in nodes_by_file[file]:
            rendered_nodes_table += '\n'
            rendered_nodes_table += ';'.join(node.values())+';'+file
    return rendered_nodes_table, rendered_node_headers


def get_new_nodes(prompt, nodes_by_file, headers=["type", "name", "inputs", "outputs", "parent class", "is parent", "short description"], relevant_files_and_folders=None):
    GET_NEW_NODES_PROMPT_FORMAT = """from this nodes (variables, functions, classes, ...) add nodes that would need to be created to complete the task
- if none is required respond None
- make sure to give them a descriptive name
- give them a name that a senior developer would give
- create them in files that can then be reused
task:
{task}
relevant files and folders:
{relevant_files_and_folders}
nodes:
{nodes}
result:
{headers}
"""
    # TODO: let it know relevant directories
    # prompt
    rendered_nodes_table, _ = render_nodes_table(
        nodes_by_file)
    relevant_nodes_prompt = GET_NEW_NODES_PROMPT_FORMAT.format(
        task=prompt, nodes=rendered_nodes_table, headers=';'.join(headers), relevant_files_and_folders='\n'.join(relevant_files_and_folders))

    response = gpt(relevant_nodes_prompt, max_tokens=MAX_TOKENS - len(relevant_nodes_prompt),
                   temperature=0)
    # clean response
    try:
        new_nodes = []
        for new_node in response.split('\n'):
            attrs = [x.strip() for x in new_node.split(';')]
            new_nodes.append(
                dict(zip(headers, attrs))
            )
        return new_nodes
    except Exception as e:
        print('ERROR get_new_nodes', e)


def get_task_clarifications(prompt):
    return gpt(TASK_CLARIFICATIONS.format(prompt=prompt), max_tokens=1000)


def print_task_steps(node_steps):
    print("# modifying")
    existing_nodes = [
        node_step for node_step in node_steps if node_step.get('exists')]
    if len(existing_nodes) > 0:
        print(dict_to_csv(existing_nodes, delimiter='\t'))
    else:
        print("-")

    print("# creating:")
    new_nodes = [
        node_step for node_step in node_steps if not node_step.get('exists')]
    if len(new_nodes) > 0:
        print(dict_to_csv(new_nodes, delimiter='\t'))
    else:
        print("-")


def dict_to_csv(data, headers=None, delimiter=';'):
    # Get headers from the specified headers, or use the keys of the first dictionary in the list if headers is not specified
    headers = headers if headers is not None else list(
        data[0].keys()) if data else []

    # Create a StringIO object for writing the CSV
    csv_buffer = StringIO()
    writer = csv.DictWriter(
        csv_buffer, fieldnames=headers, delimiter=delimiter)

    # Write the headers and the data to the buffer
    writer.writeheader()
    for row in data:
        row_data = {header: row[header] for header in headers}
        writer.writerow(row_data)

    # Get the contents of the buffer and return it as a string
    csv_str = csv_buffer.getvalue()
    return csv_str


def get_task_plan_steps(prompt, relevant_nodes, new_nodes):
    TASK_PLAN_STEPS = """steps to complete the task
task: {prompt}
relevant resources:
{nodes}

steps example format:
resource name; step description; dependent on resources
greater; add a username string input and then print it with a greater message; 
bulk_greater; receive many usernames and calls the greater function for each one of them; greater
main; add a call to the bulk_greater function with the names karl, leo and juliet; bulk_greater, greater

steps:
resource name; step description; dependent on resources
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
                                     "type", "name", "inputs", "outputs", "parent class", "short description", "file"], delimiter=';')
    rendered_steps_prompt = TASK_PLAN_STEPS.format(
        prompt=prompt, nodes=rendered_new_nodes)
    raw_steps = gpt(rendered_steps_prompt,
                    max_tokens=MAX_TOKENS - len(rendered_steps_prompt))

    # join response data to nodes
    node_names = [node['name'] for node in nodes]
    for raw_step in raw_steps.split("\n"):
        name, task_step_description, dependencies = [
            x.strip() for x in raw_step.split(";")]
        for i, node in enumerate(nodes):
            if node['name'] == name:
                nodes[i]['task_step_description'] = task_step_description
                nodes[i]['dependencies'] = [dependency.strip(
                ) for dependency in dependencies if dependency.strip() in node_names]
                yield nodes[i]


def get_task_plan(prompt, target_dir, relevant_files=None, relevant_nodes=None, new_nodes=None, exclude_files=None, rexclude_files=None, print_plan=False, debug=INFO):
    # Relevant files
    if not relevant_files:
        relevant_files, calls = get_relevant_files(
            prompt, target_dir, exclude_files=exclude_files, rexclude_files=rexclude_files)
        if debug:
            print("relevant_files calls", calls)
    if debug:
        print("relevant_files:", relevant_files)

    # Relevant nodes in files
    if not relevant_nodes:
        relevant_nodes = get_relevant_nodes(prompt, relevant_files)
    if debug:
        print("relevant_nodes:", relevant_nodes)

    # New nodes
    if not new_nodes:
        new_nodes = get_new_nodes(
            prompt, relevant_nodes, relevant_files_and_folders=relevant_files)
    if debug:
        print("new_nodes:", new_nodes)
    steps = get_task_plan_steps(prompt, relevant_nodes, new_nodes)
    steps = list(steps)

    if print_plan:
        print_task_steps(steps)
    return steps

def execute_task_plan(prompt, steps):
    for step in steps:
        if not os.path.exists(step['file']):
            os.makedirs(os.path.dirname(step['file']), exist_ok=True)
            content = ""
        else:
            with open(step['file']) as f:
                content = f.read()
        dependency_nodes = [dependency_node for dependency_node in steps if dependency_node['name'] in step['dependencies']]
        rendered_dependency_nodes = dict_to_csv(dependency_nodes, headers=[
                                     "type", "name", "inputs", "outputs", "parent class", "short description", "file"], delimiter=';')
        if step.get('exists'):
            instruction = f"""
current file: {step['file']}
modify the {step['type']} named {step['name']}
inputs {step['inputs']} 
outputs {step['outputs']} 
parent class {step['parent class']} 
task: {step['task_step_description']}
relevant resources:
{rendered_dependency_nodes}
"""
        else:
            instruction = f"""
current file: {step['file']}
code a {step['type']} named {step['name']} that {step['short description']}
inputs {step['inputs']} 
outputs {step['outputs']} 
parent class {step['parent class']} 
task: {step['task_step_description']}
relevant resources:
{rendered_dependency_nodes}
"""
        edited_file = code_edit_gpt(content, instruction, max_tokens=MAX_TOKENS - len(instruction))
        # print("INSTRUCTIONS", instruction)
        # print("NAME:",step['name'])
        # print("CONTENT:")
        print(edited_file)


def fulfill_task(prompt, target_dir, steps=False, ask_for_clarifications=False, relevant_files=None, relevant_nodes=None, new_nodes=None, exclude_files=[], rexclude_files=[], ask_confirmation=True):

    if ask_for_clarifications:
        clarifications = get_task_clarifications(prompt)
        print(clarifications)
        return

    # last_iteration, logs, plan = iterative_planning(
    #    prompt, target_dir, max_iterations=40, manual=False, exclude_files=exclude_files, rexclude_files=rexclude_files)

    if not steps:
        steps = get_task_plan(prompt, target_dir, relevant_files=relevant_files, relevant_nodes=relevant_nodes, new_nodes=new_nodes,
                              exclude_files=exclude_files, rexclude_files=rexclude_files, print_plan=ask_confirmation)
    else:
        if ask_confirmation:
            print_task_steps(steps)
    if ask_confirmation:
        confirmation = input("apply (y,N)") == "y"
        if not confirmation:
            return

    execute_task_plan(prompt, steps)


if __name__ == '__main__':
    if True:
        fulfill_task(
            "add a Sieve of Eratosthenes method to find primes",
            './sample/project',
            steps=[{'type': 'function', 'name': 'sieve_of_eratosthenes', 'inputs': 'number_limit', 'outputs': 'primes', 'parent class': 'None', 'is parent': 'False', 'short description': 'Finds primes using the Sieve of Eratosthenes algorithm.',
                    'file': './sample/project/utils/primes/sieve_of_eratosthenes.py', 'task_step_description': 'add a function to find primes using the Sieve of Eratosthenes algorithm.', 'dependencies': []}],
            rexclude_files=['migrations', 'tests', '__pycache__',
                            '.git', 'media', '.env', 'node_modules', 'build', '.cache']
        )
    if False:
        nodes = get_new_nodes("add a Sieve of Eratosthenes method to find primes", {'./sample/project/utils/fibonacci/cows.py': [
                              {'type': 'function', 'name': 'fibonacci_cows', 'inputs': 'n:int', 'outputs': 'cows:list', 'parent class': " ' '", 'is parent': 'true', 'short description': " ' '"}]})
        print(nodes)
