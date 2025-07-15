# Individual GitHub repo for MGTA 495

This is a practice repo, just for you ...

## Keyboard short-cut

Copy-and-pasting commands into a terminal can a bit cumbersome. To facilitate the process, you can add a keyboard shortcut to VS Code to send code to a terminal. Use the command palette and type "Preferences: Open Keyboard Shortcuts (JSON)". If this file is empty, you can copy and paste the below into the file and save it. If you already have shortcuts defined, add just the dictionaries and save the keyboard shortcut file. Once the shortcut is defined, you can use CMD+Enter on macOS and CTRL+Enter on Windows to send the command under the cursor to the terminal or you can select multiple lines to send.

```python
[
    {
        "key": "cmd+enter",
        "command": "workbench.action.terminal.runSelectedText",
        "when": "editorLangId == 'shellscript' || editorLangId == 'markdown' && isMac"
    },
    {
        "key": "ctrl+enter",
        "command": "workbench.action.terminal.runSelectedText",
        "when": "editorLangId == 'shellscript' || editorLangId == 'markdown' && !isMac"
    },
]
```

## Technical details

For Milestone 2 and beyond, we will be using UV for python package management. UV works on Windows, macOS, and Linux. First, open a terminal and determine if UV is already accessible:

```bash
uv --version
```

If you see a version number (e.g., 0.6.x), proceed to the next steps. If not, you can install `uv` using the command below. Only do this, however, if you don't already have UV installed:

```bash
pip install --user uv
```

### Setup the practice repo

First, make sure that you connected VS Code to the repo you cloned from GitHub (e.g., ~/git/rsm-mgta495-xyz123). Then check that no other python environments are active. The first command below will deactivate any open "venv" environments. The second command is only needed if you use "conda" for package management

```bash
deactivate
```

```bash
conda deactivate
```

If the below does not show any output in the terminal then you can be sure that all python environments have been deactivate

```bash
echo $VIRTUAL_ENV $CONDA_PREFIX
```

Now we will create a new virtual python environment using the command below:

```bash
uv init .
uv venv --python 3.12.7  # Create virtual environment with Python 3.12.7
```

### Package Management

In VS Code, you should now be able to select the `.venv` python environment to use in the terminal, Jupyter Notebooks, python code files, etc. To use the environment in a terminal, you will need to `activate` it using the command below:

```bash
source .venv/bin/activate
```

To add packages to  the code chunk above you should be able to add python packages. The `pyrsm` package will install several dependencies that you will likely need (e.g., sklearn, pandas, etc.).

```bash
uv add pyrsm python-dotenv openai google-genai anthropic requests langchain langchain_openai langchain-google-genai langchain_anthropic langchain_community pydantic pydantic-ai ipywidgets chatlas fastmcp "mcp[cli]" smolagents "smolagents[mcp]" crawl4ai
```

To be able to use `chatlas` and `shiny` with MCP, please also run the command below to get the development version of `chatlas`:

```bash
uv add git+https://github.com/vnijs/chatlas-mcp
```

To run the `query-chat` example we need to install the querychat packages from GitHub using the command below:

```bash
uv add "querychat @ git+https://github.com/posit-dev/querychat#subdirectory=python-package"
```

To double check if the package install worked as expected, run the command below.

```bash
uv run python -c "import requests; print(requests.__version__)"
```

If your directory already has a "pyproject.toml" file you can installed all the packages listed in the project file using:

```bash
uv sync
```

Using `uv sync` is a great way to make your work reproducible by keeping your python packages synched with collaborators and others that might want to use your code in the future.

In VS Code, you should now be able to select the `.venv` python environment to use in the terminal, Jupyter Notebooks, and with `Python: Select Interpreter` from the VS Code Command Palette.

### Using dotenv to manage API Keys

Put the code below into a terminal and then copy in your API token for LLama. Make sure the API key is not shown *anywhere* in your code or notebooks! Also, NEVER push a `.env` file with keys, passwords, or secrets to GitHub.

```bash
echo "LLAMA_API_KEY=copy-your-api-token-here" >> ~/.env
```

You can get a free API key from Google Gemini at <https://aistudio.google.com/apikey>{target="_blank"}. You may need to use a personal Gmail account to access Google AI Studio. Once you have the key, add it to your `.env` file using the command below:

```bash
echo "GEMINI_API_KEY=copy-your-api-token-here" >> ~/.env
```

> Note: If you want to double check if the keys were correctly added to your `.env` file, run the command below.

```bash
code ~/.env
```

### Keys used in location and weather examples

Get an API key from <https://geocode.maps.co/account/> and add it to your `.env` files as follows

```bash
echo "GEO_API_KEY=copy-your-api-token-here" >> ~/.env
```

You do NOT need an API key to run the examples that connect to <https://open-meteo.com/>

### Commit and push changes to GitHub

At this point, you can commit your changes to git. Before you run the code below, however, make sure there is not a `.env` file in your repo and that no jupyter notebooks show any of your API keys.

```bash
git add .
git commit -m "init 2025"
git push
```

### Using UV for other projects

The standard approach for projects will be to create a new folder and setup a virtual environment specifically for that project. For example, lets say your new project will be `test_project`. You could start with the commands below:

```bash
cd ~;
mkdir test_project;
cd test_project;
```

Then initialize your project environment:

```bash
uv init .                # Initialize UV in current directory
```

```bash
uv venv --python 3.12.7  # Create virtual environment with Python 3.12.7
```

In VS Code, you should be able to select the `.venv` python environment to use in your Jupyter Notebooks. To use the environment in a terminal, you will need to `activate` it using the command below:

```bash
source .venv/bin/activate
```

Then `add` the python packages you need just like we did above. If you plan to work with Jupyter notebooks (*.ipynb files) in your new project, you will need to install notebook dependencies using the below:

```bash
uv add ipykernel jupyter
```

Common UV commands for managing packages are listed below. Note that these will give directory specific results:

```bash
uv add <package-name>    # Install a package
uv remove <package-name> # Remove a package
uv pip list              # List installed packages in current directory
uv run python-file.py    # Run a Python file using the virtual environment
```

For more information about UV watch:

* <https://www.youtube.com/watch?v=qh98qOND6MI>{target="_blank"}
* <https://www.datacamp.com/tutorial/python-uv>{target="_blank"}
* <https://github.com/astral-sh/uv>{target="_blank"}

### Trouble shooting

If, for some reason, you want to reset the project, run the below to get to the project directory of your choice. Check that the `pwd` command shows you the directory you are trying to clean up.

```bash
cd ~/test_project
pwd
```

Then run the below. Note that is a DESTRUCTIVE operation. Double and triple check that only the things you want to remove are listed below. There is NO UNDO for this operation:

```bash
rm -rf .git .venv/ .python-version main.py pyproject.toml uv.lock
```
