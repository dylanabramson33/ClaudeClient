from django import forms

class LoadPDBForm(forms.Form):
    pdb_id = forms.CharField(max_length=4, label="PDB ID")

class PyMOLQueryForm(forms.Form):
    query = forms.CharField(widget=forms.Textarea, required=True, label="PyMOL Query")