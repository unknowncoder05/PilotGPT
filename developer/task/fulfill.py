from developer.task.clarifications import get_task_clarifications
from developer.plan.task_plan import get_task_plan
from developer.plan.steps import print_task_steps
from developer.plan.execute import execute_task_plan


def fulfill_task(gpt, code_edit_gpt, prompt, target_dir, steps=False, ask_for_clarifications=False, relevant_files=None, relevant_nodes=None, new_nodes=None, exclude_files=[], rexclude_files=[], ask_confirmation=True):

    if ask_for_clarifications:
        clarifications = get_task_clarifications(gpt, prompt)
        print(clarifications)
        return

    # last_iteration, logs, plan = iterative_planning(
    #    prompt, target_dir, max_iterations=40, manual=False, exclude_files=exclude_files, rexclude_files=rexclude_files)

    if not steps:
        steps = get_task_plan(gpt, prompt, target_dir, relevant_files=relevant_files, relevant_nodes=relevant_nodes, new_nodes=new_nodes,
                              exclude_files=exclude_files, rexclude_files=rexclude_files, print_plan=ask_confirmation)
    else:
        if ask_confirmation:
            print_task_steps(steps)
    if ask_confirmation:
        confirmation = input("apply (y,N)") == "y"
        if not confirmation:
            return

    execute_task_plan(code_edit_gpt, prompt, steps)
