from project.project import Project
from developer.clarifications import get_task_clarifications
from developer.plan.task_plan import get_task_plan
from developer.plan.execute import execute_task_plan
from developer.plan.steps import log_task_steps
from developer.files.relevant import get_relevant_files
from developer.nodes.relevant import get_relevant_nodes
from developer.nodes.new_nodes import get_new_nodes
from developer.plan.steps import get_task_plan_steps
import os
from get_logger import logger

class Task:
    project: Project
    prompt: str
    commit_message: str
    planned: bool = False

    # TODO: proper types
    def __init__(self, gpt, code_edit_gpt, table_completion_gpt, selection_gpt, project: Project, prompt, commit_message=None) -> None:
        self.gpt = gpt # TODO: remove
        self.code_edit_gpt = code_edit_gpt
        self.table_completion_gpt = table_completion_gpt
        self.project = project
        self.prompt = prompt
        self.selection_gpt = selection_gpt

        if commit_message == None:
            self.commit_message = prompt
        else:
            # TODO: make gpt create a good name
            self.commit_message = commit_message
        pass
    
    def get_relevant_files(self, exclude_files=[], rexclude_files=[]):
        # Relevant files
        relevant_files = get_relevant_files(
            self.table_completion_gpt, self.prompt, self.project.repository_path,
            exclude_files=exclude_files, rexclude_files=rexclude_files
        )
        return relevant_files
    
    def get_relevant_nodes(self, relevant_files):
        # Relevant nodes in files
        relevant_nodes = get_relevant_nodes(
            prompt=self.prompt, selection_gpt=self.selection_gpt,
            table_completion_gpt=self.table_completion_gpt, relevant_files=relevant_files
        )
        return relevant_nodes
    
    def get_new_nodes(self, relevant_nodes, relevant_files):
        new_nodes = get_new_nodes(
            prompt=self.prompt, nodes=relevant_nodes, table_completion_gpt=self.table_completion_gpt,
            relevant_files_and_folders=relevant_files
        )
        return new_nodes
    
    def get_steps(self, relevant_nodes, new_nodes, ):
        steps = get_task_plan_steps(
            self.prompt, relevant_nodes, new_nodes,
            table_completion_gpt=self.table_completion_gpt
        )
        return steps
        
    def plan(self, ask_for_clarifications=False, exclude_files=[], rexclude_files=[]):
        if ask_for_clarifications:
            clarifications = get_task_clarifications(self.gpt, self.prompt)
            logger.debug(clarifications)
            return

        steps = get_task_plan(self.table_completion_gpt, self.selection_gpt, self.prompt, target_dir=self.project.repository_path,
                              exclude_files=exclude_files, rexclude_files=rexclude_files)
        self.steps = steps
        self.planned = True
        return steps

    def apply(self, ask_confirmation=True, target_branch=None, push=True):
        # TODO: divide this logic in functions
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
        # TODO: add the project specific functionalities to the project class 
        new_branch = self.project.repo.create_head(target_branch)
        self.project.repo.head.set_reference(new_branch)
        self.project.repo.head.reset(index=True, working_tree=True)
        # self.project.repo.head.reset(index=True, working_tree=True)

        logger.info(f'STEPS: {self.steps}')
        # modify files
        edited_files = []
        for file_path, file_edited_content in execute_task_plan(self.prompt, self.steps, code_edit_gpt=self.code_edit_gpt, table_completion_gpt=self.table_completion_gpt):
            # TODO: use join path

            directory = os.path.dirname(file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(file_edited_content if file_edited_content else '')
            # stage changes
            edited_files.append(os.getcwd() + '/' + file_path)

        # stage and commit changes
        self.project.repo.index.add(edited_files)
        commit_message = self.commit_message
        self.project.repo.index.commit(commit_message)

        # push
        if push:
            logger.info("Pushing")
            remote = self.project.repo.remote()
            remote.push(new_branch)

        # switch back to the original branch
        # original_branch = self.project.repo.branches[current_branch]
        # original_branch.checkout()
