# Objective
this tool is intended to write clean code for simple tasks in large projects

# GPT Code pipeline
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
- run tests, if fails go back to step 1 (not in scope)
- on failed tests, run debugging and solving software (not in scope)

## 3. security
- check for security flaws, if founds solve and go back to step 1 (not implemented)
- write security test (not implemented)

## 4. human in the loop
- human corrections, if fails solve and go back to step 1 (not in scope)

# Improvements
- if target branch is output branch, just add the commit and push
- if repository already exists, change name or make a (stage,) pull and checkout
- if branch already exits throw an error
- if nothing to push, throw an error
- checkout big projects imports
- check for different input formats and more complex requirements
- tests
