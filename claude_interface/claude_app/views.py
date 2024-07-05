import os
from django.shortcuts import render
from django.conf import settings
from .forms import ClaudeQueryForm
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from claude_client import ClaudeClient
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.core.paginator import Paginator
from django.conf import settings
import os

def query_claude(request):
    if request.method == 'POST':
        form = ClaudeQueryForm(request.POST, request.FILES)
        if form.is_valid():
            client = ClaudeClient()
            params = {}

            if form.cleaned_data['query']:
                params['query'] = form.cleaned_data['query']

            if form.cleaned_data['template']:
                template_file = form.cleaned_data['template']
                template_path = default_storage.save('templates/temp_template.txt', ContentFile(template_file.read()))
                client.template_file = os.path.join(settings.MEDIA_ROOT, template_path)

            for field in form.param_fields:
                if form.cleaned_data[field]:
                    key, value = form.cleaned_data[field].split(':', 1)
                    params[key.strip()] = value.strip()

            if form.cleaned_data['pdf_file']:
                pdf_file = form.cleaned_data['pdf_file']
                pdf_path = default_storage.save('pdfs/temp_pdf.pdf', ContentFile(pdf_file.read()))
                pdf_content = client.parse_pdf(os.path.join(settings.MEDIA_ROOT, pdf_path), form.cleaned_data['pdf_range'])
                params['pdf_content'] = pdf_content

            if form.cleaned_data['estimate_cost']:
                query = client.build_query(**params)
                token_count = len(client.tokenizer.encode(query))
                response = client.query(**params)
                output_token_count = len(client.tokenizer.encode(response))
                cost = client.estimate_cost(query, token_count, output_token_count, client.tokenizer)
                result = f"Estimated cost: ${cost:.2f}"
            else:
                result = client.query(**params)

            if form.cleaned_data['json_output']:
                result = client.parse_json(result)
            safe_result = mark_safe(result)
            return render(request, 'claude_app/result.html', {'result': safe_result})
    else:
        form = ClaudeQueryForm()

    return render(request, 'claude_app/query_form.html', {'form': form})


def view_logs(request):
    logs_file = getattr(settings, 'CLAUDE_LOGS_FILE', './logs.txt')
    
    if not os.path.exists(logs_file):
        return render(request, 'claude_app/logs.html', {'error': 'Logs file not found.'})

    with open(logs_file, 'r') as file:
        logs = file.read().split('='*80)
        logs = [log.strip() for log in logs if log.strip()]

    logs.reverse()  # Show most recent logs first

    paginator = Paginator(logs, 10)  # Show 10 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'claude_app/logs.html', {'page_obj': page_obj})