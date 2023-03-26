import openai
import os

INFO = True
TOKENS_TO_CHARACTERS = 0.75
MAX_TOKENS = 4097
RECOMMENDED_TOKENS_PER_FILE = 3000


def check_content_filter(prompt):
    if INFO:
        print('gpt call')
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
    if INFO:
        print('gpt call')
    if max_tokens == -1:
        max_tokens = int(MAX_TOKENS - len(prompt) / TOKENS_TO_CHARACTERS)
        if max_tokens < 0:
            print("ERR: long prompt", prompt)
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
    if INFO:
        print('gpt call')
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

def execute_chat_code_model(input, instruction, model, temperature=0, max_tokens=100, many=False, *args, **kwargs):
    """
    Executes the completion model with the given parameters and returns the list of responses.
    """
    if INFO:
        print('gpt call')
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
    context.append({"role": "assistant",
                "content": "The next message is the updated file you need"})

    response = openai.ChatCompletion.create(
        model=model,
        temperature=temperature,
        messages=context,
        *args, **kwargs
    )
    if many:
        return [x["message"]["content"].strip() for x in response["choices"]]
    else:
        return response["choices"][0]["message"]["content"].strip()


def open_ai_model_func(model, type='completion'):
    """
    Returns a function that executes the given model with the specified type.
    """
    if type == 'completion':
        def execute(prompt_text, *args, **kwargs):
            return execute_completion_model(prompt_text, model=model, *args, **kwargs)
        return execute
    if type == 'code_edit':
        def execute(prompt_text, instruction, *args, **kwargs):
            return execute_chat_code_model(prompt_text, instruction, model=model, *args, **kwargs)
        return execute


openai.api_key = os.getenv("OPENAPI_API_KEY")
