from developer.files.relevant import get_relevant_files
from developer.nodes.relevant import get_relevant_nodes
from developer.plan.steps import get_task_plan_steps, print_task_steps
from developer.nodes.new_nodes import get_new_nodes

# TODO: from settings
INFO = False

def get_task_plan(gpt, prompt, target_dir, relevant_files=None, relevant_nodes=None, new_nodes=None, exclude_files=None, rexclude_files=None, print_plan=False, debug=INFO):
    # Relevant files
    if not relevant_files:
        relevant_files, calls = get_relevant_files(
            gpt, prompt, target_dir, exclude_files=exclude_files, rexclude_files=rexclude_files)
        if debug:
            print("relevant_files calls", calls)
    if debug:
        print("relevant_files:", relevant_files)

    # Relevant nodes in files
    if not relevant_nodes:
        relevant_nodes = get_relevant_nodes(gpt, prompt, relevant_files)
    if debug:
        print("relevant_nodes:", relevant_nodes)

    # New nodes
    if not new_nodes:
        new_nodes = get_new_nodes(
            gpt, prompt, relevant_nodes, relevant_files_and_folders=relevant_files)
    if debug:
        print("new_nodes:", new_nodes)
    steps = get_task_plan_steps(gpt, prompt, relevant_nodes, new_nodes)
    steps = list(steps)

    if print_plan:
        print_task_steps(steps)
    return steps