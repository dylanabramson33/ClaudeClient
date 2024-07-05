import json
from django.shortcuts import render
from django.http import JsonResponse
from .forms import LoadPDBForm, PyMOLQueryForm
from claude_client import ClaudeClient
import xmlrpc.client
import os
from django.core.cache import cache
from django.conf import settings

pymol = xmlrpc.client.ServerProxy('http://localhost:9123')
# Add this function to get the template path
def get_template_path():
    return "/Users/dylanabramson/Desktop/Claude/templates/pymol.jinja"

def pymol_interface(request):
    load_form = LoadPDBForm()
    query_form = PyMOLQueryForm()
    chat_history = cache.get('chat_history', [])
    return render(request, 'claude_app/pymol_interface.html', {
        'load_form': load_form,
        'query_form': query_form,
        'chat_history': chat_history
    })

def load_pdb(request):
    if request.method == 'POST':
        form = LoadPDBForm(request.POST)
        if form.is_valid():
            pdb_id = form.cleaned_data['pdb_id']
            try:
                pymol.do(f"fetch {pdb_id}")
                pdb_dir = os.path.join(settings.BASE_DIR, 'claude_app', 'static', 'pdb_files')
                os.makedirs(pdb_dir, exist_ok=True)
                pdb_filename = f'{pdb_id}.pdb'
                pdb_path = os.path.join(pdb_dir, pdb_filename)
                pymol.do(f"save {pdb_path}")
                
                cache.set('current_pdb_id', pdb_id)
                cache.set('current_pdb_path', pdb_path)
                # Clear previous query history and chat history when loading a new PDB
                cache.set('query_history', [])
                cache.set('chat_history', [])
                return JsonResponse({'success': True, 'message': f'PDB {pdb_id} loaded successfully'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def query_claude_and_run_pymol(request):
    if request.method == 'POST':
        form = PyMOLQueryForm(request.POST)
        if form.is_valid():
            client = ClaudeClient(template_file=get_template_path())
            query = form.cleaned_data['query']

            current_pdb_id = cache.get('current_pdb_id', 'Unknown')
            current_pdb_path = cache.get('current_pdb_path', None)
            query_history = cache.get('query_history', [])
            chat_history = cache.get('chat_history', [])

            # Load PDB file content
            pdb_content = ''
            if current_pdb_path and os.path.exists(current_pdb_path):
                with open(current_pdb_path, 'r') as pdb_file:
                    pdb_content = pdb_file.read()

            # Append current query history to the context
            context = {
                'query': query,
                'pdb_id': current_pdb_id,
                'query_history': query_history,
            }

            claude_response = client.query(**context)

            try:
                response_data = json.loads(claude_response)
                pymol_commands = response_data['commands']
                explanation = response_data['explanation']
                pymol_results = execute_pymol_commands(pymol_commands)

                # Save the current state as a PDB file
                pdb_dir = os.path.join(settings.BASE_DIR, 'claude_app', 'static', 'pdb_files')
                os.makedirs(pdb_dir, exist_ok=True)
                pdb_filename = f'{current_pdb_id}_modified.pdb'
                pdb_path = os.path.join(pdb_dir, pdb_filename)
                pymol.do(f"save {pdb_path}")

                # Update query history
                query_history.append({
                    'query': query,
                    'explanation': explanation,
                    'commands': pymol_commands
                })
                cache.set('query_history', query_history)

                # Update chat history
                chat_history.append({
                    'role': 'user',
                    'content': query
                })
                chat_history.append({
                    'role': 'assistant',
                    'content': explanation,
                    'commands': pymol_commands
                })
                cache.set('chat_history', chat_history)

                return JsonResponse({
                    'explanation': explanation,
                    'pymol_results': pymol_results,
                    'current_pdb_id': current_pdb_id,
                    'pdb_path': f'/static/pdb_files/{pdb_filename}',
                    'chat_history': chat_history
                })
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid response from Claude'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def execute_pymol_commands(commands):
    results = []
    for cmd in commands:
        try:
            pymol.do(cmd)
            results.append(f"Command: {cmd}")
        except Exception as e:
            print(e)
            results.append(f"Command: {cmd}\nError: {str(e)}")
    return results