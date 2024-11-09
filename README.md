# friendly-computing-machine
slackbot


## environment
uv
```
uv venv
source .venv/bin/activate
uv sync
```
pyenv virtual environment: https://github.com/pyenv/pyenv-virtualenv
makes package management easier for test version of python
i named my environment friendly-computing-machine
```
pyenv virtualenv 3.10.7 friendly-computing-machine
```

to make version management easier between different repos, create a .python-version file locally
```
echo 'friendly-computing-machine' > .python-version
```

if your bash config is setup correctly with pyenv and pyenv-virtualenv then
you should be get the following
```
user@computer:~/friendly-computing-machine$ pyenv version
friendly-computing-machine (set by /home/user/friendly-computing-machine/.python-version)
```

run setup.py
```
pip install -e .
```

your environment is now setup

## run
run the bot (or whatever this currently is)
```
python run.py
```
