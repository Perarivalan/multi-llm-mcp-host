# Multi-LLM MCP Host

A Python command-line chat host that connects an LLM to tools exposed by a local Model Context Protocol (MCP) server. The host starts the MCP server as a child process and communicates with it over standard input/output.

## Project Structure

```text
.
|-- config.json          # Default provider, model, and provider model lists
|-- config_manager.py    # Configuration loading, CLI arguments, and menus
|-- handlers.py          # Tool implementations and dispatch
|-- host.py              # Interactive chat host and LLM/MCP orchestration
|-- llm_factory.py       # Provider-specific LLM client creation
|-- mcp_client.py        # MCP client and stdio server connection
|-- mcp_server.py        # MCP server and tool registration
|-- requirements.txt     # Required Python packages
`-- tools/
    |-- __init__.py      # Tool exports
    |-- figma.py         # Figma/design tool schemas
    `-- telemetry.py     # Telemetry tool schemas
```

Local-only files and folders:

- `.env` stores API credentials. It is ignored by Git and must be created separately on each machine.
- `.venv/` stores the local Python environment. It is ignored by Git and should be recreated on each machine or after changing Python versions.
- `__pycache__/` contains generated Python bytecode and does not need to be transferred.

## Prerequisites

- Python installed on the machine. Use a Python version supported by the installed dependencies; the repository does not currently pin a specific Python version.
- A terminal. PowerShell is used in the Windows instructions below.
- A Gemini API key for the default provider. Other providers require their own credentials or local service.
- Internet access for installing packages and using hosted LLM providers.
- Git only if cloning the repository. Git is not required if you receive the source another way.
- VS Code is optional. Node.js/npm are not required; this project does not currently include a frontend.

The provider and model names shown in `config.json` are configuration choices. Check with the provider that a listed model is still available to your account.

## Set Up on Windows

Open PowerShell in the project directory. If you are cloning the repository, clone it first and change into the cloned directory.

Check installed Python versions:

```powershell
py --list
```

Create a virtual environment using an installed version. Replace `3.14` with the version you intend to use:

```powershell
py -3.14 -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
```

Create a `.env` file in the project root and add your own key:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Do not commit or share `.env`. Keep API keys out of source code, screenshots, and terminal transcripts. If a key is exposed, revoke it with the provider and create a replacement.

Start the application:

```powershell
& ".\.venv\Scripts\python.exe" host.py
```

The interactive menu lets you select a provider, model, and temperature. You can also pass provider/model settings directly, for example:

```powershell
& ".\.venv\Scripts\python.exe" host.py --provider gemini --model gemini-3.5-flash-lite
```

To use the environment's shorter `python` command, activate it in PowerShell from the project directory:

```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .\.venv\Scripts\Activate.ps1)
python host.py
```

The execution-policy change applies only to the current PowerShell process. Alternatively, invoke the virtual environment's Python executable directly as shown earlier.

## Set Up on macOS or Linux

From the project directory, create and install into a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create `.env` in the project root with your provider key, then run:

```bash
python host.py
```

## Optional LLM Providers

`requirements.txt` installs the MCP SDK, Gemini SDK, and `python-dotenv`. The following provider clients are optional and are not installed by the base requirements:

```powershell
# Choose the package for the provider you intend to use.
& ".\.venv\Scripts\python.exe" -m pip install openai
& ".\.venv\Scripts\python.exe" -m pip install anthropic
& ".\.venv\Scripts\python.exe" -m pip install ollama
```

Set the matching key in `.env` for OpenAI (`OPENAI_API_KEY`) or Anthropic (`ANTHROPIC_API_KEY`). Ollama requires the Ollama application/service and a model available locally. Install only the optional package(s) you need.

## Move to Another PC or Workspace

Transfer or clone the project source. Do not transfer `.venv/`, `.env`, or `__pycache__/`:

1. Install Python and, if cloning, Git on the new machine.
2. Create a new `.venv` on that machine using its installed Python version.
3. Install dependencies from `requirements.txt`.
4. Create a new local `.env` with that machine's own API key.
5. Select the new `.venv` interpreter in VS Code if using VS Code: run **Python: Select Interpreter** and choose the interpreter under the project folder.
6. Run `host.py` using that environment.

The MCP child process uses the same Python interpreter as the host, so launching the host from the project virtual environment also gives the MCP server its installed packages.

## Upgrade Python or Rebuild `.venv`

Installing a new Python version does not change an existing `.venv`. Recreate the environment to ensure it uses the new interpreter. First stop the app. If the environment is active in the terminal, run `deactivate` before continuing.

On Windows, replace `3.14` with the new installed version:

```powershell
py --list
if (Test-Path .\.venv) { Remove-Item -Recurse -Force .\.venv }
py -3.14 -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" --version
& ".\.venv\Scripts\python.exe" host.py
```

On macOS or Linux, use the new Python executable and remove only this project's environment before recreating it:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python --version
python host.py
```

Rebuilding is usually the cleanest way to keep `.venv` small: install only packages listed in `requirements.txt` and optional provider packages you actually use. Do not copy package files manually between Python versions. Keep dependency requirements updated when adding packages; for strictly repeatable production installs, use a dependency lock file in addition to the current unpinned requirements.

## Current Scope

The tool schemas are in `tools/`, and their handlers are in `handlers.py`. The health, error, Figma-file, component, and design-token handlers currently return sample data; they are not connected to live monitoring or Figma services. Gemini is the primary demonstrated tool-calling path. Other provider adapters are present, but their tool-call conversation flows may need additional implementation and testing before relying on them.