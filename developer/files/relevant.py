import os

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

def get_relevant_files(gpt, prompt, target_dir, exclude_files=[], rexclude_files=[]):
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
