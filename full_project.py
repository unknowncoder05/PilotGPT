import re
import openai
import os

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


FASTAPI_PYTHON_FILES_STRUCTURE_FORMAT = """using fastapi and python create api "{prompt}" the following files are needed (include tests):
./docker-compose.yml
./README.md
./__init__.py
./.env
./Dockerfile
./requirements.txt
"""
FASTAPI_PYTHON_FILES_CONTENT_FORMAT = """using fastapi and python create api "{prompt}" with the following file structure:
{files}

file: ./docker-compose.yml
content >>>
version: '3'

volumes:
  local_postgres_data: {{ }}
  local_postgres_data_backups: {{ }}

services:
  postgres:
    image: postgres:11.6

  api: &api
    build:
      context: ./
      dockerfile: ./Dockerfile
    image: generated-api
    depends_on:
      - postgres
    volumes:
      - ./app:/app
    env_file:
      - ./.env
    ports:
      - "80:80"
    command: python3 main.py

<<<
"""

openai.api_key = os.getenv("OPENAPI_API_KEY")
gpt = open_ai_model_func("text-davinci-002")


def get_files(prompt):
    rendered_prompt = FASTAPI_PYTHON_FILES_STRUCTURE_FORMAT.format(
        prompt=prompt)
    res = gpt(rendered_prompt, max_tokens=500, temperature=0)
    result_files = [x.strip()
                    for x in re.findall(r'\./.*\n', rendered_prompt+res)]
    raw_files = result_files
    return list(set(raw_files))


def parse_file_content(string: str) -> dict:
    files = {}
    current_file = None
    current_content = []
    for line in string.split('\n'):
        if line.startswith('file:'):
            if current_file is not None:
                files[current_file] = '\n'.join(current_content)
            current_file = line.split(':')[1].strip()
            current_content = []
        elif line == 'content >>>':
            continue
        elif line == '<<<':
            continue
        else:
            current_content.append(line)
    if current_file is not None:
        files[current_file] = '\n'.join(current_content)
    return files


def get_files_content(prompt, files):
    files_string = '\n'.join(files)
    rendered_prompt = FASTAPI_PYTHON_FILES_CONTENT_FORMAT.format(
        prompt=prompt, files=files_string)
    res = gpt(rendered_prompt, max_tokens=2000, temperature=0)
    print('code res length', len(res))
    files_with_content = parse_file_content(rendered_prompt+res)
    return files_with_content


def write_files(files: dict, target_dir: str):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    for file, content in files.items():
        full_path = os.path.join(target_dir, file.replace('./', ''))
        directory = os.path.dirname(full_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(full_path, 'w') as f:
            f.write(content)


def create_project(prompt, target_dir):
    files = get_files(prompt)
    print(files)
    content = get_files_content(prompt, files)
    print(content)
    write_files(content, target_dir)


if __name__ == '__main__':
    create_project("basic crud", './build')
