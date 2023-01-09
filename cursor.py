import ast
import re
import openai
import os
from utils.node_description import tree_node_names


def check_content_filter(prompt):
    completions = openai.Completion.create(
        engine="content-filter-alpha",
        prompt=prompt,
        max_tokens=1,
        temperature=0,
        top_p=0
    )
    return completions.choices[0].text


def execute_completion_model(prompt, model="code-davinci-002", temperature=1, max_tokens=100, many=False, *args, **kwargs):
    """
    Executes the completion model with the given parameters and returns the list of responses.
    """
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


def open_ai_model_func(model, type='completion'):
    """
    Returns a function that executes the given model with the specified type.
    """
    if type == 'completion':
        def execute(prompt_text, *args, **kwargs):
            return execute_completion_model(prompt_text, model=model, *args, **kwargs)
        return execute
    if type == 'code_completion':
        def execute(prompt_text, *args, **kwargs):
            return execute_completion_model(prompt_text, model=model, *args, **kwargs)
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


def list_directory_recursively(dir_path: str, exclude_files=[], rexclude_files=[]):
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

TASK_PLAN = """for the following feature, for each file write what code is needed to develop it, follow the step format, if needed add more than one action per file
step format:
{{
    "file": "./file",
    "action": "action to be taken",
    "results": [{{"name": "expected name of created item", "type": "class/variable/function/etc", "inputs": [], "outputs": []}}]
 }}
feature:
{prompt}
files:
{files}
json plan:
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

RELEVANT_DIRECTORIES = """to develop the following feature which files are relevant, keep in mind this are not all the available files so if no relevant file is found, return "None", list them in a single line like "./file,./file2"
feature: {prompt}
files:
{files}
result:
-"""

openai.api_key = os.getenv("OPENAPI_API_KEY")
gpt = open_ai_model_func("text-davinci-002")

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
        if current_token_count + item_token_count > max_tokens:
            yield current_list
            current_list = []
            current_token_count = 0
        current_list.append(item)
        current_token_count += item_token_count


def get_relevant_directories(prompt, target_dir, exclude_files=[], rexclude_files=[]):
    files = list_directory_recursively(
        target_dir, exclude_files=exclude_files, rexclude_files=rexclude_files)
    initial_tokens = (len(RELEVANT_DIRECTORIES) +
                      len(prompt)) / TOKENS_TO_CHARACTERS
    expected_tokens = 3000-initial_tokens

    relevant_directories = []
    calls = 0
    for chunk_of_files in slice_list_by_tokens(files, max_tokens=expected_tokens):
        calls += 1
        relevant_files_prompt = RELEVANT_DIRECTORIES.format(
            prompt=prompt, files="\n".join([x.replace(target_dir+"/", "") for x in chunk_of_files]))
        response = gpt(relevant_files_prompt, max_tokens=MAX_TOKENS - len(relevant_files_prompt),
                       temperature=0, stop=['\n'])
        if response and "None" not in response:
            # TODO: proper cleaning
            relevant_directories.extend(
                [x.strip().replace('./', '') for x in response.split(",")])
    return relevant_directories, calls


def get_task_clarifications(prompt):
    return gpt(TASK_CLARIFICATIONS.format(prompt=prompt))


def get_task_plan(prompt, relevant_directories):
    plan = gpt(TASK_PLAN.format(prompt=prompt, files='\n'.join(relevant_directories)))
    return plan


def fulfill_task(prompt, target_dir, exclude_files=[], rexclude_files=[]):

    if False:
        clarifications = get_task_clarifications(prompt)
        print(clarifications)

    # last_iteration, logs, plan = iterative_planning(
    #    prompt, target_dir, max_iterations=40, manual=False, exclude_files=exclude_files, rexclude_files=rexclude_files)

    if True:
        #relevant_directories, calls = get_relevant_directories(
        #    prompt, target_dir, exclude_files=exclude_files, rexclude_files=rexclude_files)
        relevant_directories = ['api/api/users/views/authentication.py']
        print(relevant_directories)
        
        # plan = get_task_plan(prompt, relevant_directories)
        plan = """{
    "file": "./api/api/users/views/authentication.py",
    "action": "add a public endpoint called 'health' that returns 'ok'",
    "results": [{"name": "health", "type": "endpoint", "inputs": [], "outputs": ["ok"]}]
}"""
        print(plan)


if __name__ == '__main__':
    fulfill_task(
        "add a public endpoint called \"health\" that returns ok in the user app",
        '/home/unknown-dev/Desktop/storage/YERSON/TMF/Sempros/sempros-backend-api',
        rexclude_files=['migrations', 'tests', '__pycache__',
                        '.git/', 'media', '.env', 'node_modules']
    )
