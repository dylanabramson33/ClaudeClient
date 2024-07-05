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

def get_django_project_structure(root_dir):
    project_structure = {}
    git_files = set(get_git_tracked_files(root_dir))
    
    for file_path in git_files:
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

# Usage
django_project_path = '/path/to/your/django/project'
project_structure = get_django_project_structure(django_project_path)
output_project_structure(project_structure)