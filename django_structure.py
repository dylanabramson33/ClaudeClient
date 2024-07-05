import os
import json
import subprocess

def get_git_tracked_files(root_dir):
    try:
        result = subprocess.run(['git', 'ls-files'], cwd=root_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Error running git ls-files: {result.stderr}")
            return []
        return result.stdout.splitlines()
    except Exception as e:
        print(f"Error: {e}")
        return []

def is_important_django_file(file_path):
    important_extensions = {'.py', '.html', '.css', '.js', '.txt', '.md', '.yml', '.yaml', '.json'}
    important_filenames = {'Dockerfile', 'docker-compose.yml', '.gitignore', 'requirements.txt'}
    
    _, ext = os.path.splitext(file_path)
    filename = os.path.basename(file_path)
    
    if ext in important_extensions or filename in important_filenames:
        # Exclude common database files
        if filename.endswith('.sqlite3') or filename.endswith('.db'):
            return False
        # Exclude migration files
        if 'migrations' in file_path.split(os.sep) and filename != '__init__.py':
            return False
        return True
    return False

def get_django_project_structure(root_dir):
    project_structure = {}
    git_files = set(get_git_tracked_files(root_dir))
    
    for file_path in git_files:
        if not is_important_django_file(file_path):
            continue
        
        full_path = os.path.join(root_dir, file_path)
        parts = file_path.split(os.sep)
        current_dir = project_structure
        
        for part in parts[:-1]:
            if part not in current_dir:
                current_dir[part] = {}
            current_dir = current_dir[part]
        
        if '__files__' not in current_dir:
            current_dir['__files__'] = []
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                current_dir['__files__'].append({
                    'name': parts[-1],
                    'content': content
                })
        except Exception as e:
            print(f"Error reading {full_path}: {e}")

    return project_structure

def output_project_structure(project_structure):
    print(json.dumps(project_structure, indent=2))


import json
import os

def update_files_from_diff(original_json, diff_json):
    # Load the original and diff JSON data
    original = json.loads(original_json)
    diff = json.loads(diff_json)

    # Function to recursively update nested dictionaries
    def update_dict(original, updates):
        for key, value in updates.items():
            if isinstance(value, dict) and key in original:
                update_dict(original[key], value)
            else:
                original[key] = value

    # Update the original data with the diff
    update_dict(original, diff)

    # Function to write content to a file
    def write_file(path, content):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)

    # Update the files
    for app_name, app_data in original.items():
        if isinstance(app_data, dict):
            if "__files__" in app_data:
                for file_info in app_data["__files__"]:
                    file_path = os.path.join(app_name, file_info["name"])
                    write_file(file_path, file_info["content"])
            
            if "templates" in app_data:
                for template_app, template_data in app_data["templates"].items():
                    if "__files__" in template_data:
                        for file_info in template_data["__files__"]:
                            file_path = os.path.join(app_name, "templates", template_app, file_info["name"])
                            write_file(file_path, file_info["content"])

    print("Files updated successfully!")
# Usage
django_project_path = 'claude_interface'
project_structure = get_django_project_structure(django_project_path)
diff = {
  "claude_app": {
    "__files__": [
      {
        "name": "views.py",
        "content": "import os\nfrom django.shortcuts import render\nfrom django.conf import settings\nfrom .forms import ClaudeQueryForm, PDBUploadForm\nfrom django.core.files.storage import default_storage\nfrom django.core.files.base import ContentFile\nfrom claude_client import ClaudeClient\nfrom django.utils.safestring import mark_safe\nfrom django.shortcuts import render\nfrom django.core.paginator import Paginator\nfrom django.conf import settings\nimport os\n\ndef query_claude(request):\n    if request.method == 'POST':\n        form = ClaudeQueryForm(request.POST, request.FILES)\n        if form.is_valid():\n            # ... (existing code remains unchanged)\n    else:\n        form = ClaudeQueryForm()\n\n    pdb_form = PDBUploadForm()\n    return render(request, 'claude_app/query_form.html', {'form': form, 'pdb_form': pdb_form})\n\n# ... (existing view_logs function remains unchanged)\n\ndef view_pdb(request):\n    if request.method == 'POST':\n        form = PDBUploadForm(request.POST, request.FILES)\n        if form.is_valid():\n            pdb_file = form.cleaned_data['pdb_file']\n            pdb_path = default_storage.save('pdbs/temp_pdb.pdb', ContentFile(pdb_file.read()))\n            pdb_url = default_storage.url(pdb_path)\n            return render(request, 'claude_app/view_pdb.html', {'pdb_url': pdb_url})\n    return render(request, 'claude_app/query_form.html', {'error': 'Invalid PDB file'})"
      },
      {
        "name": "forms.py",
        "content": "from django import forms\n\nclass ClaudeQueryForm(forms.Form):\n    # ... (existing code remains unchanged)\n\nclass PDBUploadForm(forms.Form):\n    pdb_file = forms.FileField(label='Upload PDB File')"
      },
      {
        "name": "urls.py",
        "content": "from django.contrib import admin\nfrom django.urls import path\nfrom . views import query_claude, view_logs, view_pdb\n\nurlpatterns = [\n    path('admin/', admin.site.urls),\n    path('', query_claude, name='query_claude'),\n    path('logs/', view_logs, name='view_logs'),\n    path('view_pdb/', view_pdb, name='view_pdb'),\n]\n"
      }
    ],
    "templates": {
      "claude_app": {
        "__files__": [
          {
            "name": "query_form.html",
            "content": "{% extends 'claude_app/base.html' %}\n\n{% block title %}Claude Query Interface{% endblock %}\n\n{% block content %}\n    <h1>Claude Query Interface</h1>\n    <ul class=\"nav nav-tabs\" id=\"myTab\" role=\"tablist\">\n        <li class=\"nav-item\" role=\"presentation\">\n            <button class=\"nav-link active\" id=\"query-tab\" data-bs-toggle=\"tab\" data-bs-target=\"#query\" type=\"button\" role=\"tab\" aria-controls=\"query\" aria-selected=\"true\">Query</button>\n        </li>\n        <li class=\"nav-item\" role=\"presentation\">\n            <button class=\"nav-link\" id=\"pdb-tab\" data-bs-toggle=\"tab\" data-bs-target=\"#pdb\" type=\"button\" role=\"tab\" aria-controls=\"pdb\" aria-selected=\"false\">PDB Upload</button>\n        </li>\n    </ul>\n    <div class=\"tab-content\" id=\"myTabContent\">\n        <div class=\"tab-pane fade show active\" id=\"query\" role=\"tabpanel\" aria-labelledby=\"query-tab\">\n            <form method=\"post\" enctype=\"multipart/form-data\">\n                {% csrf_token %}\n                {{ form.as_p }}\n                <button type=\"button\" id=\"add-param\">Add Parameter</button>\n                <input type=\"submit\" value=\"Submit Query\">\n            </form>\n        </div>\n        <div class=\"tab-pane fade\" id=\"pdb\" role=\"tabpanel\" aria-labelledby=\"pdb-tab\">\n            <form method=\"post\" action=\"{% url 'view_pdb' %}\" enctype=\"multipart/form-data\">\n                {% csrf_token %}\n                {{ pdb_form.as_p }}\n                <input type=\"submit\" value=\"Upload PDB\">\n            </form>\n        </div>\n    </div>\n\n    <p>\n        <a href=\"{% url 'view_logs' %}\">View Logs</a>\n    </p>\n\n{% endblock %}\n\n{% block extra_js %}\n    <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js\"></script>\n    <script>\n        // ... (existing JavaScript code remains unchanged)\n    </script>\n{% endblock %}\n"
          },
          {
            "name": "view_pdb.html",
            "content": "{% extends 'claude_app/base.html' %}\n\n{% block title %}PDB Viewer{% endblock %}\n\n{% block content %}\n    <h1>PDB Viewer</h1>\n    <div id=\"viewport\" style=\"width:100%; height:400px;\"></div>\n    <script src=\"https://unpkg.com/ngl@0.10.4/dist/ngl.js\"></script>\n    <script>\n        document.addEventListener(\"DOMContentLoaded\", function() {\n            var stage = new NGL.Stage(\"viewport\");\n            stage.loadFile(\"{{ pdb_url }}\", {defaultRepresentation: true});\n        });\n    </script>\n{% endblock %}"
          },
          {
            "name": "base.html",
            "content": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <!-- ... (existing head content remains unchanged) -->\n    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css\" rel=\"stylesheet\">\n    <style>\n        /* ... (existing styles remain unchanged) */\n    </style>\n</head>\n<body>\n    <!-- ... (existing body content remains unchanged) -->\n</body>\n</html>"
          }
        ]
      }
    }
  }
}
output_project_structure(project_structure)
update_files_from_diff(project_structure,diff)