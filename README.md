# Objective
this tool is intended to write clean code for simple tasks in large projects using LLMs

# LLM Planning pipeline
0. pull the git repo
1. get relevant files
2. get relevant nodes/resources (functions, variables, classes...) ina format easily manageable
    - get from cache
    - detect file change
    - save to cache
3. plan the creation of new nodes/resources
    - use the same file structure
4. plan the steps to complete the tasks with this resources
5. run the code pipeline for each step

# LLM Code pipeline
## 1. write code
- optimize (not implemented)
- add type (not implemented)


## 2. human readable (before quality since changes to logic might happen)
- clean code and make it human readable
- relevant comments
- add documentation (not implemented)

## 3. quality
- check for bugs, if founds solve them
- write test (not implemented)
- run tests, if fails go back to step 1 (not in current scope)
- on failed tests, run debugging and solving software (not in current scope)

## 3. security
- check for security flaws, if founds solve and go back to step 1 (not implemented)
- write security test (not implemented)

## 4. human in the loop
- human corrections, if fails solve and go back to step 1 (not in current scope)

# Improvements
- allow more LLMs, currently only chatgpt available
- different developer modes: add a "raw mode" that takes all the code base and directly solves the problem (we lose control but the run is as good as the model it uses. Good for small projects, horrible for bigger ones)
- if target branch is output branch, just add the commit and push
- if repository already exists, change name or make a (stage,) pull and checkout
- if branch already exist throw an error
- if nothing to push, throw an error
- limit pricing and tokens
- checkout big projects imports
- check for different input formats and more complex requirements
- tests
