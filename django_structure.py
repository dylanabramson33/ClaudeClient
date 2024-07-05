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

def apply_diff(original, diff, base_dir):

    def apply_file_diff(file_path, file_content, file_diff):
        if isinstance(file_content, str):
            lines = file_content.split('\n')
        else:
            lines = file_content['content'].split('\n')

        if 'insert' in file_diff:
            for insert in file_diff['insert']:
                if 'after' in insert:
                    index = next(i for i, line in enumerate(lines) if insert['after'] in line)
                    lines.insert(index + 1, insert['text'])
                elif 'position' in insert and insert['position'] == 'new_file':
                    lines = insert['text'].split('\n')

        if 'modify' in file_diff:
            for modify in file_diff['modify']:
                index = next(i for i, line in enumerate(lines) if modify['find'] in line)
                lines[index] = modify['replace']

        content = '\n'.join(lines)

        # Actually write the changes to the file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)

        return content

    for app_name, app_data in diff.items():
        if '__files__' in app_data:
            for file_info in app_data['__files__']:
                file_name = file_info['name']
                file_diff = file_info['content']
                file_path = os.path.join(base_dir, app_name, file_name)
                original_file = next(f for f in original[app_name]['__files__'] if f['name'] == file_name)
                original_file['content'] = apply_file_diff(file_path, original_file['content'], file_diff)

        if 'templates' in app_data:
            for template_app, template_data in app_data['templates'].items():
                if '__files__' in template_data:
                    for file_info in template_data['__files__']:
                        file_name = file_info['name']
                        file_diff = file_info['content']
                        file_path = os.path.join(base_dir, app_name, 'templates', template_app, file_name)
                        original_template = next((f for f in original[app_name]['templates'][template_app]['__files__'] if f['name'] == file_name), None)
                        if original_template is None:
                            original[app_name]['templates'][template_app]['__files__'].append({
                                'name': file_name,
                                'content': apply_file_diff(file_path, '', file_diff)
                            })
                        else:
                            original_template['content'] = apply_file_diff(file_path, original_template['content'], file_diff)

    print("Files updated successfully!")
    return json.dumps(original, indent=2)
    
django_project_path = 'claude_interface'
project_structure = get_django_project_structure(django_project_path)
diff = {
  "claude_app": {
    "__files__": [
      {
        "name": "views.py",
        "content": {
          "insert": [
            {
              "after": "from .forms import ClaudeQueryForm",
              "text": ", PDBUploadForm"
            },
            {
              "after": "    return render(request, 'claude_app/query_form.html', {'form': form})",
              "text": "\n\ndef view_pdb(request):\n    if request.method == 'POST':\n        form = PDBUploadForm(request.POST, request.FILES)\n        if form.is_valid():\n            pdb_file = form.cleaned_data['pdb_file']\n            pdb_path = default_storage.save('pdbs/temp_pdb.pdb', ContentFile(pdb_file.read()))\n            pdb_url = default_storage.url(pdb_path)\n            return render(request, 'claude_app/view_pdb.html', {'pdb_url': pdb_url})\n    return render(request, 'claude_app/query_form.html', {'error': 'Invalid PDB file'})"
            }
          ],
          "modify": [
            {
              "find": "    return render(request, 'claude_app/query_form.html', {'form': form})",
              "replace": "    pdb_form = PDBUploadForm()\n    return render(request, 'claude_app/query_form.html', {'form': form, 'pdb_form': pdb_form})"
            }
          ]
        }
      },
      {
        "name": "forms.py",
        "content": {
          "insert": [
            {
              "after": "        self.param_fields.append(field_name)",
              "text": "\n\nclass PDBUploadForm(forms.Form):\n    pdb_file = forms.FileField(label='Upload PDB File')"
            }
          ]
        }
      },
      {
        "name": "urls.py",
        "content": {
          "modify": [
            {
              "find": "from . views import query_claude",
              "replace": "from . views import query_claude, view_pdb"
            },
            {
              "find": "    path('logs/', view_logs, name='view_logs'),",
              "replace": "    path('logs/', view_logs, name='view_logs'),\n    path('view_pdb/', view_pdb, name='view_pdb'),"
            }
          ]
        }
      }
    ],
    "templates": {
      "claude_app": {
        "__files__": [
          {
            "name": "query_form.html",
            "content": {
              "modify": [
                {
                  "find": "<h1>Claude Query Interface</h1>",
                  "replace": "<h1>Claude Query Interface</h1>\n    <ul class=\"nav nav-tabs\" id=\"myTab\" role=\"tablist\">\n        <li class=\"nav-item\" role=\"presentation\">\n            <button class=\"nav-link active\" id=\"query-tab\" data-bs-toggle=\"tab\" data-bs-target=\"#query\" type=\"button\" role=\"tab\" aria-controls=\"query\" aria-selected=\"true\">Query</button>\n        </li>\n        <li class=\"nav-item\" role=\"presentation\">\n            <button class=\"nav-link\" id=\"pdb-tab\" data-bs-toggle=\"tab\" data-bs-target=\"#pdb\" type=\"button\" role=\"tab\" aria-controls=\"pdb\" aria-selected=\"false\">PDB Upload</button>\n        </li>\n    </ul>\n    <div class=\"tab-content\" id=\"myTabContent\">\n        <div class=\"tab-pane fade show active\" id=\"query\" role=\"tabpanel\" aria-labelledby=\"query-tab\">"
                },
                {
                  "find": "    </form>",
                  "replace": "    </form>\n        </div>\n        <div class=\"tab-pane fade\" id=\"pdb\" role=\"tabpanel\" aria-labelledby=\"pdb-tab\">\n            <form method=\"post\" action=\"{% url 'view_pdb' %}\" enctype=\"multipart/form-data\">\n                {% csrf_token %}\n                {{ pdb_form.as_p }}\n                <input type=\"submit\" value=\"Upload PDB\">\n            </form>\n        </div>\n    </div>"
                }
              ],
              "insert": [
                {
                  "after": "{% block extra_js %}",
                  "text": "\n    <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js\"></script>"
                }
              ]
            }
          },
          {
            "name": "view_pdb.html",
            "content": {
              "insert": [
                {
                  "position": "new_file",
                  "text": "{% extends 'claude_app/base.html' %}\n\n{% block title %}PDB Viewer{% endblock %}\n\n{% block content %}\n    <h1>PDB Viewer</h1>\n    <div id=\"viewport\" style=\"width:100%; height:400px;\"></div>\n    <script src=\"https://unpkg.com/ngl@0.10.4/dist/ngl.js\"></script>\n    <script>\n        document.addEventListener(\"DOMContentLoaded\", function() {\n            var stage = new NGL.Stage(\"viewport\");\n            stage.loadFile(\"{{ pdb_url }}\", {defaultRepresentation: true});\n        });\n    </script>\n{% endblock %}"
                }
              ]
            }
          }
        ]
      }
    }
  }
}

original_json = output_project_structure(project_structure)
updated_json = apply_diff(original_json, json.dumps(diff), django_project_path)