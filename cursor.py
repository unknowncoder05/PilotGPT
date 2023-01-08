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


TASK_CLARIFICATIONS = """for the implementation of this feature, the possible previous clarifications required before starting would be:
feature:
{prompt}
clarifications:

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

TOKENS_TO_CHARACTERS = 0.75
MAX_TOKENS = 4097
RECOMMENDED_TOKENS_PER_FILE = 3000

def file_description(file_name):
    if file_name.endswith(".py"):
        return tree_node_names(file_name)
    else:
        return "not a python file"

# ask the ai to explore a project and decide which files a re relevant
def planning_stage(prompt, target_dir, debug=False, manual=False, input_field="in:", output_field="out:", exclude_files=[], rexclude_files=[], max_iterations=20):
    initial_files = list_directory_items(target_dir, exclude_files=exclude_files, rexclude_files=rexclude_files)
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
                files = list_directory_items(file_name, exclude_files=exclude_files, rexclude_files=rexclude_files)
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


def fulfill_task(prompt, target_dir, exclude_files=[], rexclude_files=[]):

    # clarifications = TASK_CLARIFICATIONS.format(prompt=prompt)
    # print(clarifications)
    last_iteration, logs, plan = planning_stage(prompt, target_dir, max_iterations=40, manual=False, exclude_files=exclude_files, rexclude_files=rexclude_files)
    print("RESULT")
    print(logs)
    print("plan", plan)
    print("last_iteration", last_iteration)


if __name__ == '__main__':
    fulfill_task("add an endpoint called \"health\" that returns ok",
                 '/home/unknown-dev/Desktop/storage/YERSON/TMF/Sempros/sempros-backend-api', rexclude_files=['migrations', 'tests', '__pycache__'])
