from developer.task import Task
from project.project import Project
from gpt.models import open_ai_model_func
import os
import sys


if __name__ == '__main__':
    repository_url = sys.argv[1]
    task_prompt = sys.argv[2]
    if len(sys.argv) < 3:
        print("Usage: python main.py <repository_url> <task_prompt>")
        sys.exit(1)

    gpt = open_ai_model_func("text-davinci-002")
    code_edit_gpt = open_ai_model_func(
        "code-davinci-edit-001", type="code_edit")
    project = Project(repository_path=repository_url)
    task = Task(
        gpt,
        code_edit_gpt,
        project=project,
        prompt=task_prompt,
    )
    task.plan(rexclude_files=['migrations', 'tests', '__pycache__',
                              '.git', 'media', '.env', 'node_modules', 'build', '.cache'])

    task.apply(target_branch='TASK-1')
