FROM python:3.8-alpine

WORKDIR /app

RUN apk update
RUN apk add git

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . /app

# CMD [ "python", "/app/main.py", "$REPOSITORY_URL", "$TASK_PROMPT"]