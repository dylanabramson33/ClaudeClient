from django.urls import path
from .views import pymol_interface, load_pdb, query_claude_and_run_pymol, execute_commands

urlpatterns = [
    path('', pymol_interface, name='pymol_interface'),
    path('load_pdb/', load_pdb, name='load_pdb'),
    path('query_claude_and_run_pymol/', query_claude_and_run_pymol, name='query_claude_and_run_pymol'),
    path('execute_commands/', execute_commands, name='execute_commands'),

]