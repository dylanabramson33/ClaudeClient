from django import forms

class LoadPDBForm(forms.Form):
    pdb_id = forms.CharField(max_length=4, label="PDB ID")

class PyMOLQueryForm(forms.Form):
    query = forms.CharField(widget=forms.Textarea(attrs={
            'class': 'form-control no-resize',
            'id': 'id_query',
            'placeholder': 'Enter your query here...'
        }), required=True, label="PyMOL Query")