from django import forms

class ClaudeQueryForm(forms.Form):
    query = forms.CharField(widget=forms.Textarea, required=False)
    template = forms.FileField(required=False)
    json_output = forms.BooleanField(required=False)
    pdf_file = forms.FileField(required=False)
    pdf_range = forms.CharField(required=False)
    estimate_cost = forms.BooleanField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.param_fields = []

    def add_param_field(self):
        field_name = f'param_{len(self.param_fields)}'
        self.fields[field_name] = forms.CharField(required=False)
        self.param_fields.append(field_name)
