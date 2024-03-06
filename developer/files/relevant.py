import os
from get_logger import logger

# TODO: from settings
TOKENS_TO_CHARACTERS = 0.75
MAX_TOKENS = 4097


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


def get_relevant_files(table_completion_gpt, prompt, target_dir=None, files=None, exclude_files=[], rexclude_files=[], minimum_file_relevance_rating=2):
    GET_RELEVANT_FILES = """get the relevant files (files that might need to be modified or that contain tools or architectures needed to complete the task) for this software development task: {prompt}"""
    # either target_dir or files should be set
    if not files:
        files = list_files_recursively(
            target_dir, exclude_files=exclude_files, rexclude_files=rexclude_files)
    relevant_directories = []

    # optimize file names since for the model "./long/project/path/file.py" and "./file.py" mean the same but is cheaper
    # TODO: detect automatically the project path
    if target_dir:
        optimized_file_names = [
            {"title": x.replace(target_dir+"/", "")} for x in files]
    else:
        optimized_file_names = [{"title": x} for x in files]

    # table generation
    raw_relevant_files = table_completion_gpt(
        GET_RELEVANT_FILES.format(prompt=prompt),
        max_tokens=-1,
        temperature=0,
        headers=["file_name", "relevance_rating"],
        verbose_headers=["file name (string:required)", "relevance rating[0,10] (int)"],
        context_tables=[
            {
                "name": "related files",
                "data": optimized_file_names
            },
        ],
        extra_requirements = ["relevance rating should be a numeric value"],
        chunk_able=True
    )
    logger.debug(f"optimized file names: {optimized_file_names}")
    logger.debug(f"raw relevant files: {raw_relevant_files}")
    if raw_relevant_files:
        # TODO: proper cleaning
        for file_response in raw_relevant_files:
            # get the original base path back
            if target_dir:
                file_name = target_dir+'/' + \
                    file_response['file_name'].replace('./', '')
            else:
                file_name = file_response['file_name']
            if not os.path.exists(file_name):
                continue
            relevance_rating = file_response.get('relevance_rating', '0')
            if type(relevance_rating) == str and relevance_rating.isnumeric():
                relevance_rating = int(relevance_rating)
            if type(relevance_rating) == int:
                continue
            if  relevance_rating > minimum_file_relevance_rating:
                relevant_directories.append(file_name)
    return relevant_directories
