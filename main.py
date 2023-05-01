from developer.task import Task
from project.project import Project
from gpt.models import open_ai_model_func
from db import change_task_status, TaskStatus
import sys
from get_logger import logger
import traceback

print("LOG TEST")
if __name__ == '__main__':
    if len(sys.argv) != 5 + 1:
        logger.error(
            "Usage: python main.py <repository_url> <task_prompt> <input_branch> <output_branch> <id>")
        sys.exit(1)
    repository_url = sys.argv[1]
    task_prompt = sys.argv[2]
    input_branch = sys.argv[3]
    output_branch = sys.argv[4]
    task_id = sys.argv[5]
    logger.debug(f"""task_id={task_id}
task_prompt={task_prompt}
input_branch={input_branch}
output_branch={output_branch}
"""
                 )

    try:
        gpt = open_ai_model_func("text-davinci-002")
        code_edit_gpt = open_ai_model_func(
            "gpt-3.5-turbo", type="code_edit")
        table_completion_gpt = open_ai_model_func(
            "gpt-3.5-turbo", type="table_completion")
        selection_gpt = open_ai_model_func(
            "gpt-3.5-turbo", type="selection_gpt")

        project = Project(
            repository_url=repository_url,
            repository_path='repo',
            branch=input_branch,
        )
        task = Task(
            gpt=gpt,
            code_edit_gpt=code_edit_gpt,
            table_completion_gpt=table_completion_gpt,
            selection_gpt=selection_gpt,
            project=project,
            prompt=task_prompt,
        )
        task.plan(rexclude_files=['migrations', 'tests', '__pycache__',
                                  '.git', 'media', '.env', 'node_modules', 'build', '.cache'])

        task.apply(target_branch=output_branch, ask_confirmation=False)
        change_task_status(task_id)
    except Exception as e:
        logger.error(traceback.format_exc())
        change_task_status(task_id, TaskStatus.ERROR.value[0], str(e))
