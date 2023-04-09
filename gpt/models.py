import openai
import os
import re
from get_logger import logger
from utils.csv_to_list import csv_to_list
from utils.dict_to_csv import dict_to_csv

openai.api_key = os.getenv("OPENAPI_API_KEY")
TOKENS_TO_CHARACTERS = 0.75
MAX_TOKENS = 4097
RECOMMENDED_TOKENS_PER_FILE = 3000


def check_content_filter(prompt):
    logger.debug('gpt call')
    completions = openai.Completion.create(
        engine="content-filter-alpha",
        prompt=prompt,
        max_tokens=1,
        temperature=0,
        top_p=0
    )
    return completions.choices[0].text


def execute_completion_model(prompt, model="code-davinci-002", temperature=0, max_tokens=-1, many=False, *args, **kwargs):
    """
    Executes the completion model with the given parameters and returns the list of responses.
    """
    logger.debug('gpt call')
    if max_tokens == -1:
        max_tokens = int(MAX_TOKENS - len(prompt) / TOKENS_TO_CHARACTERS)
        if max_tokens < 0:
            logger.error(f'long prompt: {prompt}')
            return ''

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


def execute_code_edit_model(input, instruction, model="code-davinci-edit-001", temperature=0, max_tokens=100, many=False, *args, **kwargs):
    """
    Executes the completion model with the given parameters and returns the list of responses.
    """
    logger.debug('gpt call')
    if max_tokens == -1:
        max_tokens = int(MAX_TOKENS - len(input) / TOKENS_TO_CHARACTERS)
        if max_tokens < 0:
            logger.error(f'long prompt: {input}')
            return ''
    
    response = openai.Edit.create(
        model=model,
        input=input,
        temperature=temperature,
        instruction=instruction,
        *args, **kwargs
    )
    if many:
        return [x.text.strip() for x in response.choices]
    else:
        return response.choices[0].text.strip()

def gpt3_5_tables(context: list, headers: list, model="gpt-3.5-turbo", context_tables=[], verbose_headers=[], many=False, max_tokens=100, temperature=0, chunk_able=False,*args, **kwargs):
    # TODO: if chunk_able=True divide the data into chunks and make multiple calls 
    logger.debug('gpt call')
    if max_tokens == -1:
        max_tokens = int(MAX_TOKENS - len(context) / TOKENS_TO_CHARACTERS)
        if max_tokens < 0:
            logger.error(f'long prompt: {context}')
            return ''
        
    delimiter = ","
    expected_result_type = "table"
    # this is used so the model generates no extra explanations
    start_token, end_token = "START", "END"
    empty_response_token = start_token+" "+end_token
    rendered_headers = delimiter.join(
        headers if verbose_headers else verbose_headers)

    if context_tables:
        rendered_context_tables = []
        for context_table in context_tables:
            if not context_table['data']:
                continue
            rendered_context_table = context_table['name'] + '\n' + \
                dict_to_csv(context_table['data'], delimiter=delimiter)
            rendered_context_tables.append(rendered_context_table)
        if rendered_context_table:
            context_tables_messages = [
                {"role": "system", "content": "use this related data if needed" + '\n' + '\n'.join(rendered_context_tables)}]
        else:
            context_tables_messages = []

    else:
        context_tables_messages = []

    messages = [
        {"role": "system", "content": "You are a software planning assistant"},
        {"role": "user", "content": context},
        {"role": "system", "content": f"limit yourself to just complete the rows based on the columns {rendered_headers}"},
        {"role": "system", "content": f"use a line per row"},
        {"role": "system", "content": f"if no row can be generated, just write {empty_response_token}"},
        {"role": "system", "content": f"expected response format = {expected_result_type}"},
        {"role": "system", "content": f"the {expected_result_type} should start with {start_token} and should end in {end_token}"},
        *context_tables_messages,
        {"role": "assistant", "content": rendered_headers},
    ]
    # log_messages(messages)
    response = openai.ChatCompletion.create(
        model=model,
        temperature=0.2,
        messages=messages,
    )

    def clean_response(raw_response):
        if raw_response == expected_result_type:
            return []
        raw_rows = re.sub(f"^START\s*|\s*END$", "", raw_response).split('\n')
        raw_table = [delimiter.join(headers)] + raw_rows
        return csv_to_list(raw_table)

    if many:
        return [
            clean_response(choice["message"]["content"])
            for choice in response["choices"]
        ]
    else:
        raw_response = response["choices"][0]["message"]["content"]
        return clean_response(raw_response)

def execute_chat_code_model(input, instruction, model, temperature=0, max_tokens=100, many=False, *args, **kwargs):
    """
    Executes the completion model with the given parameters and returns the list of responses.
    """
    logger.debug('gpt call')
    context = [
        {"role": "system", "content": "You are a senior software developer assistant that generates generates code files."},
        {"role": "user", "content": instruction},

    ]
    if input:
        context.extend([
            {"role": "assistant",
                "content": "Give me the current file content if it exists"},
            {"role": "user", "content": input},
        ])
    context.extend([{"role": "system", "content": "limit yourself to just generate usable code with no extra text"},
                    {"role": "system", "content": "expected response format = file"},
                    {"role": "system", "content": "the file should start with START and should end in END"},])

    response = openai.ChatCompletion.create(
        model=model,
        temperature=temperature,
        messages=context,
        *args, **kwargs
    )
    if many:
        return [x["message"]["content"].strip() for x in response["choices"]]
    else:
        raw_code = response["choices"][0]["message"]["content"].strip()
        raw_code = re.sub(f"^START\s*|\s*END$", "", raw_code)
        return raw_code.strip()


def open_ai_model_func(model, type='completion'):
    """
    Returns a function that executes the given model with the specified type.
    """
    if type == 'completion':
        def execute(prompt_text, *args, **kwargs):
            return execute_completion_model(prompt_text, model=model, *args, **kwargs)
        return execute
    if type == 'table_completion':
        def execute(prompt_text, *args, **kwargs):
            return gpt3_5_tables(prompt_text, model=model, *args, **kwargs)
        return execute
    if type == 'code_edit':
        def execute(prompt_text, instruction, *args, **kwargs):
            return execute_chat_code_model(prompt_text, instruction, model=model, *args, **kwargs)
        return execute
