from project.project import Project
from developer.clarifications import get_task_clarifications
from developer.plan.task_plan import get_task_plan
from developer.plan.execute import execute_task_plan
from developer.plan.steps import log_task_steps
import os
from get_logger import logger


class Task:
    project: Project
    prompt: str
    commit_message: str
    planned: bool = False

    # TODO: proper types
    def __init__(self, gpt, code_edit_gpt, table_completion_gpt, project: Project, prompt, commit_message=None) -> None:
        self.gpt = gpt
        self.code_edit_gpt = code_edit_gpt
        self.table_completion_gpt = table_completion_gpt
        self.project = project
        self.prompt = prompt

        if commit_message == None:
            self.commit_message = prompt
        else:
            # TODO: make gpt create a good name
            self.commit_message = commit_message
        pass

    def plan(self, ask_for_clarifications=False, exclude_files=[], rexclude_files=[]):
        if ask_for_clarifications:
            clarifications = get_task_clarifications(self.gpt, self.prompt)
            logger.debug(clarifications)
            return

        steps = get_task_plan(self.gpt,self.table_completion_gpt, self.prompt, target_dir=self.project.repository_path,
                              exclude_files=exclude_files, rexclude_files=rexclude_files)
        self.steps = steps
        self.planned = True
        return steps

    def apply(self, ask_confirmation=True, target_branch=None, push=True):
        if not self.planned:
            raise Exception("you have to plan this task before executing it")

        # log plan and ask for confirmation
        if ask_confirmation:
            log_task_steps(self.steps)
            confirmation = input("apply (y,N)") == "y"
            if not confirmation:
                return

        # save the name of the current branch
        # current_branch = self.project.repo.active_branch.name

        # create a new branch and switch to it
        new_branch = self.project.repo.create_head(target_branch)
        self.project.repo.head.set_reference(new_branch)
        self.project.repo.head.reset(index=True, working_tree=True)
        # self.project.repo.head.reset(index=True, working_tree=True)

        logger.info(f'STEPS: {self.steps}')
        # modify files
        edited_files = []
        for file_name, file_edited_content in execute_task_plan(self.code_edit_gpt, self.prompt, self.steps):
            # TODO: use join path
            with open(self.project.repository_path + '/' + file_name, 'w') as f:
                f.write(file_edited_content)
            # stage changes
            edited_files.append(os.getcwd() + '/' +
                                self.project.repository_path + '/' + file_name)

        # stage and commit changes
        self.project.repo.index.add(edited_files)
        commit_message = self.commit_message
        self.project.repo.index.commit(commit_message)

        # push
        if push:
            logger.info("Pushing")
            self.project.repo.remote().push(new_branch)

        # switch back to the original branch
        # original_branch = self.project.repo.branches[current_branch]
        # original_branch.checkout()
