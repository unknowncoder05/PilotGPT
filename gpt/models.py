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


def gpt3_5_tables(context: list, headers: list, model="gpt-3.5-turbo", context_tables=[], verbose_headers=[], many=False, max_tokens=100, empty_field_response_token="", extra_requirements=[], temperature=0, chunk_able=False, *args, **kwargs):
    # TODO: if chunk_able=True divide the data into chunks and make multiple calls
    # TODO: validate verbose_headers and headers have the same length
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
        if rendered_context_tables:
            context_tables_messages = [
                {"role": "system", "content": "use this related data if needed" + '\n' + '\n'.join(rendered_context_tables)}]
        else:
            context_tables_messages = []

    else:
        context_tables_messages = []

    messages = [
        {"role": "system", "content": f"You are a software planning assistant who generates {expected_result_type}"},
        {"role": "user", "content": context},
        {"role": "system", "content": f"limit yourself to just complete the rows based on the columns {rendered_headers}"},
        {"role": "system", "content": f"use a line per row"},
        {"role": "system", "content": f"if a field can not be generated, just write {empty_field_response_token}"},
        {"role": "system", "content": f"if no row can be generated, just left {empty_response_token if empty_response_token else 'empty space'}"},
        {"role": "system", "content": f"expected response format = {expected_result_type}"},
        {"role": "system", "content": f"the {expected_result_type} should start with {start_token} and should end in {end_token}"},
        *context_tables_messages,
        *[{"role": "system", "content":extra_requirement} for extra_requirement in extra_requirements],
        {"role": "system", "content": f"since your output is going to be transform into a table, follow the column format strictly otherwise bad things will happen"},
        {"role": "assistant", "content": rendered_headers},
    ]
    # log_messages(messages)
    response = openai.ChatCompletion.create(
        model=model,
        temperature=0.2,
        messages=messages,
    )
    logger.debug(f"gpt raw response: {response}")

    def clean_response(raw_response):
        if raw_response == expected_result_type:
            return []
        # extract just relevant code
        raw_rows = re.sub(f"^START\s*|\s*END$", "", raw_response).split('\n')
        # remove spaces between rows
        raw_rows = [re.sub(r'\s*,\s*|\s*,|,\s*', ',', raw_row) for raw_row in raw_rows]
        raw_table = [delimiter.join(headers)] + raw_rows
        return csv_to_list(raw_table, headers=headers)

    if many:
        return [
            clean_response(choice["message"]["content"])
            for choice in response["choices"]
        ]
    else:
        raw_response = response["choices"][0]["message"]["content"]
        return clean_response(raw_response)


def gpt3_5_table_rows_selection(context: list, options_table: dict, selector_field_index=0, headers=None, verbose_headers=None, model="gpt-3.5-turbo", context_tables=[], many=False, max_tokens=100, empty_field_response_token="", temperature=0, chunk_able=False, *args, **kwargs):
    # TODO: if chunk_able=True divide the data into chunks and make multiple calls
    # TODO: validate verbose_headers and headers have the same length
    # TODO: validate if selector_field_index is valid
    logger.debug('gpt call')
    if max_tokens == -1:
        max_tokens = int(MAX_TOKENS - len(context) / TOKENS_TO_CHARACTERS)
        if max_tokens < 0:
            logger.error(f'long prompt: {context}')
            return ''

    delimiter = ","
    delimiter_verbose = "comma"
    expected_result_type = f"{delimiter_verbose} separated values"
    # this is used so the model generates no extra explanations
    start_token, end_token = "START", "END"
    empty_response_token = start_token+" "+end_token

    if not headers:
        headers = list(options_table[0].keys())
    
    if not verbose_headers:
        verbose_headers = verbose_headers if verbose_headers else headers
    selector_field_verbose = verbose_headers[selector_field_index]
    selector_field = headers[selector_field_index]

    # render context table messages
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
    rendered_options_table = dict_to_csv(options_table, delimiter=delimiter)
    messages = [
        {"role": "system", "content": "You are a selector assistant"},
        {"role": "user", "content": context},
        {"role": "user", "content": rendered_options_table},
        {"role": "system", "content": f"if no row can be generated, just left {empty_response_token if empty_response_token else 'empty space'}"},
        {"role": "system", "content": f"expected response is a single line of {expected_result_type} of the identifier column '{selector_field_verbose}'"},
        {"role": "system", "content": f"if an option is not relevant enough, don't add it"},
        {"role": "system", "content": f"expected response format = '{expected_result_type}'"},
        {"role": "system", "content": f"the '{expected_result_type}' should start with {start_token} and should end in {end_token}"},
        *context_tables_messages,
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
        raw_row = re.sub(f"^START\s*|\s*END$", "", raw_response)
        list_of_selected_option = []
        for raw_option_key in raw_row.split(delimiter):
            option_key = raw_option_key.strip()

            # check options in table
            for option in options_table:
                if option[selector_field] == option_key:
                    list_of_selected_option.append(option)
                    break
        return list_of_selected_option

    if many:
        return [
            clean_response(choice["message"]["content"])
            for choice in response["choices"]
        ]
    else:
        raw_response = response["choices"][0]["message"]["content"]
        return clean_response(raw_response)


def extract_text_between_tokens(text, start_token, end_token):
    pattern = re.escape(start_token) + "(.*?)" + re.escape(end_token)
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return None


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
                    {"role": "system", "content": "the output file should start with the literal words START and should end in END, since the output is going to be processed with a regex, nothing else you write is going to be used"},])

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
        raw_code = extract_text_between_tokens(raw_code, "START", "END")
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
    if type == 'selection_gpt':
        def execute(prompt_text, *args, **kwargs):
            return gpt3_5_table_rows_selection(prompt_text, model=model, *args, **kwargs)
        return execute
