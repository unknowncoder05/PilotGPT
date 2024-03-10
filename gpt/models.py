import openai
from openai import OpenAI
import os
import re
from get_logger import logger
from utils.csv_to_list import csv_to_list
from utils.dict_to_csv import dict_to_csv
import json

openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
TOKENS_TO_CHARACTERS = 0.75
RECOMMENDED_TOKENS_PER_FILE = 3000

def json_string_get_attribute(json_string, attribute):
    try:
        json_object = json.loads(json_string)
    except Exception as e:
        raise Exception(f"LLM response is not json serializable: {json_string} {e}")
    if attribute not in json_object:
        raise Exception(f"LLM has no '{attribute}' key: {json_object}")
    return json_object[attribute]

def check_content_filter(prompt):
    logger.debug('gpt_check_content_filter call')
    completions = openai.Completion.create(
        engine="content-filter-alpha",
        prompt=prompt,
        max_tokens=1,
        temperature=0,
        top_p=0
    )
    return completions.choices[0].text


def execute_completion_model(prompt, model="code-davinci-002", temperature=0, max_tokens=None, many=False, *args, **kwargs):
    """
    Executes the completion model with the given parameters and returns the list of responses.
    """
    logger.debug('gpt_execute_completion_model call')
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


def execute_code_edit_model(input, instruction, model="code-davinci-edit-001", temperature=0, max_tokens=None, many=False, *args, **kwargs):
    """
    Executes the completion model with the given parameters and returns the list of responses.
    """
    logger.debug('gpt_code_edit_model call')

    response = openai.Edit.create(
        model=model,
        input=input,
        temperature=temperature,
        instruction=instruction,
        max_tokens=max_tokens,
        *args, **kwargs
    )
    if many:
        return [x.text.strip() for x in response.choices]
    else:
        return response.choices[0].text.strip()


def gpt_tables(
        context: list,
        headers: list,
        model="gpt-3.5-turbo",
        context_tables=[],
        verbose_headers=[],
        many=False,
        max_tokens=None,
        empty_field_response_token="",
        extra_requirements=[],
        temperature=0,
        chunk_able=False, *args, **kwargs):
    """
    completes a table and returns a lsit of objects
    """
    # TODO: if chunk_able=True divide the data into chunks and make multiple calls
    # TODO: validate verbose_headers and headers have the same length
    logger.debug('gpt_tables call')

    delimiter = ","
    # this is used so the model generates no extra explanations
    rendered_headers = delimiter.join(headers)

    rendered_context_tables = []
    context_tables_messages = []
    if context_tables:
        for context_table in context_tables:
            if not context_table['data']:
                continue
            rendered_context_table = context_table['name'] + '\n' + \
                dict_to_csv(context_table['data'], delimiter=delimiter)
            rendered_context_tables.append(rendered_context_table)
        if rendered_context_tables:
            context_tables_messages = [
                {"role": "system", "content": "use this related data if needed" + '\n' + '\n'.join(rendered_context_tables)}]

    messages = [
        {"role": "system", "content": f"You are a software planning assistant who returns a json with a 'table' key that is a list of objects"},
        {"role": "system", "content": f"each object in the list should have the attributes {headers} which are defined like {verbose_headers}"},
        {"role": "user", "content": context},
        {"role": "system", "content": f"if a field can not be generated, just write {empty_field_response_token}"},
        *context_tables_messages,
        *[{"role": "system", "content":extra_requirement} for extra_requirement in extra_requirements],
        {"role": "assistant", "content": rendered_headers},
    ]
    response = client.chat.completions.create(
        model=model,
        response_format={ "type": "json_object" },
        temperature=temperature,
        max_tokens=max_tokens,
        messages=messages,
    )
    logger.debug({'messages':messages, 'content':response.choices[0].message.content})

    if many:
        return [
            json_string_get_attribute(choice.message.content, 'table')
            for choice in response.choices
        ]
    else:
        raw_response = json_string_get_attribute(response.choices[0].message.content, 'table')
        return raw_response


def gpt_table_rows_selection(context: list, options_table: dict, selector_field_index=0, headers=None, verbose_headers=None, model="gpt-3.5-turbo", context_tables=[], many=False, max_tokens=None, empty_field_response_token="", temperature=0, chunk_able=False, *args, **kwargs):
    # TODO: if chunk_able=True divide the data into chunks and make multiple calls
    # TODO: validate verbose_headers and headers have the same length
    # TODO: validate if selector_field_index is valid
    logger.debug('gpt_table_rows_selection call')

    delimiter = ","
    # this is used so the model generates no extra explanations

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
        {"role": "system", "content": f"You are a software planning assistant who returns a json with a 'selected' key that is a list of {selector_field_verbose}"},
        {"role": "user", "content": context},
        {"role": "user", "content": rendered_options_table},
        {"role": "system", "content": f"if an option is not relevant enough, don't add it"},
        *context_tables_messages,
    ]
    # log_messages(messages)
    response = client.chat.completions.create(
        model=model,
        response_format={ "type": "json_object" },
        temperature=temperature,
        max_tokens=max_tokens,
        messages=messages,
    )

    def clean_response(response_list):
        list_of_selected_option = []
        for raw_option_key in response_list:
            option_key = raw_option_key.strip()

            # check options in table
            for option in options_table:
                if option[selector_field] == option_key:
                    list_of_selected_option.append(option)
                    break
        return list_of_selected_option


    if many:
        return [
            clean_response(json_string_get_attribute(choice.message.content, 'selected'))
            for choice in response.choices
        ]
    else:
        return clean_response(json_string_get_attribute(response.choices[0].message.content, 'selected'))


def extract_text_between_tokens(text, start_token, end_token):
    pattern = re.escape(start_token) + "(.*?)" + re.escape(end_token)
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return None


def execute_chat_code_model(input, instruction, model, temperature=0, max_tokens=None, many=False, *args, **kwargs):
    """
    Executes the completion model with the given parameters and returns the list of responses.
    """
    logger.debug('gpt_code_model call')
    context = [
        {"role": "system", "content": "You are a senior software developer assistant that generates generates code files."},
        {"role": "system", "content": "Return a JSON with a 'file' key"},
        {"role": "user", "content": instruction},
    ]
    if input:
        context.extend([
            {"role": "assistant",
                "content": "Give me the current file content if it exists"},
            {"role": "user", "content": input},
        ])
    context.extend([
        {"role": "system", "content": "limit yourself to just generate usable code with no extra text"},
    ])

    response = client.chat.completions.create(
        response_format={ "type": "json_object" },
        model=model,
        temperature=temperature,
        messages=context,
        max_tokens=max_tokens,
        *args, **kwargs
    )
    if many:
        return [json_string_get_attribute(choice.message.content, 'file') for choice in response.choices]
    else:
        code = json_string_get_attribute(response.choices[0].message.content, 'file')
        return code


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
            return gpt_tables(prompt_text, model=model, *args, **kwargs)
        return execute
    if type == 'code_edit':
        def execute(prompt_text, instruction, *args, **kwargs):
            return execute_chat_code_model(prompt_text, instruction, model=model, *args, **kwargs)
        return execute
    if type == 'selection_gpt':
        def execute(prompt_text, *args, **kwargs):
            return gpt_table_rows_selection(prompt_text, model=model, *args, **kwargs)
        return execute
