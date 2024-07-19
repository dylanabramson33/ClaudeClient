# ClaudePyMOLClient

ClaudePyMOLClient provides a web interface for interacting with PyMOL using Claude AI commands

## Project Overview
With ClaudePyMOLClient we can:
- Upload molecular structure files
- Visualize molecules using PyMOL
- Interact with PyMOL using natural language commands processed by Claude AI
- Perform advanced PyMOL operations through simple text instructions

## Installation

To set up this project, follow these steps:

1. Clone the repository:
  ```
  git clone https://github.com/yourusername/pymol-claude-django-interface.git
  cd ClaudePyMOLClient
  ```
2. Create a conda environment and install dependencies:
  ```
  conda env create -f environment.yml
  conda activate pymol_claude_env
  ```
3. Install additional pip requirements:
  ```
  pip install -e .
  ```
4. Add Anthropic API key
  ```
  export ANTHROPIC_API_KEY="..."
  ```
6. Set up the Django database :
  ```
  cd claude_interface
  python manage.py makemigrations
  python manage.py migrate
  ```
7. Run server
  ```
  python manage.py runserver
  ```
8. Run pyMOL with xml-rpc server (open new terminal)
  ```
  pymol -R
  ```
9. Navigate in browser to http://127.0.0.1:8000/
   
