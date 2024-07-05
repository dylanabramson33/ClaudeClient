import pandas as pd
from jinja2 import Template
import anthropic
import json
import argparse
import sys
import os
from PyPDF2 import PdfReader
import tiktoken



class ClaudeClient:
    def __init__(self, template_file=None, max_tokens=4096):
        self.template = None
        if template_file:
            with open(template_file) as f:
                template_string = f.read()
            self.template = Template(template_string)
        self.client = anthropic.Anthropic()
        self.max_tokens = max_tokens
        self.tokenizer = tiktoken.encoding_for_model("gpt-4o")  # A close approximation for Claude
        self.logs_file = "./logs.txt"

    def build_query(self, **kwargs):
        if self.template:
            return self.template.render(**kwargs)
        else:
            return kwargs.get('query', '')

    def query(self, **kwargs):
        q = self.build_query(**kwargs)
        print(q)
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=self.max_tokens,
            messages=[
                {"role": "user", "content": q}
            ]
        )
        response = response.content[0].text

        with open(self.logs_file, "a") as f:
            f.write(f"Query: {q}\n")
            f.write(f"Response: {response}\n\n")
            f.write("=" * 80 + "\n\n")
        return response

    def parse_json(self, json_text):
        json_text = json_text.replace('\\n', '\n').replace("\\'", "'")
        try:
            json_object = json.loads(json_text)
            return json_object
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}", file=sys.stderr)
            return None

    @staticmethod
    def parse_pdf(pdf_path, char_range=None):
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            if char_range:
                start, end = map(int, char_range.split('-'))
                text = text[start:end]
            
            return text
        except Exception as e:
            print(f"Error parsing PDF: {e}", file=sys.stderr)
            return None

    @staticmethod
    def output_pdf_with_positions(text):
        lines = text.split('\n')
        position = 0
        for line in lines:
            print(f"{position:<6}: {line}")
            position += len(line) + 1  # +1 for the newline character

    @staticmethod
    def estimate_cost(q, token_count, output_token_count, tokenizer):
        token_count = len(tokenizer.encode(q))
        # Pricing for Claude 3-5 Sonnet (as of March 2024)
        # These prices may change, so it's an estimate
        price_per_1k_tokens_input = 0.03
        price_per_1k_tokens_output = 0.06
        
        # Assuming output is roughly half of input for estimation
        
        cost = (token_count / 1000 * price_per_1k_tokens_input) + \
               (output_token_count / 1000 * price_per_1k_tokens_output)
        
        return cost

def main():
    parser = argparse.ArgumentParser(description="Claude Client")
    parser.add_argument("-q", "--query", help="Direct query to Claude (used when no template is provided)")
    parser.add_argument("-t", "--template", help="Path to the template file")
    parser.add_argument("-j", "--json", action="store_true", help="Parse output as JSON")
    parser.add_argument("-p", "--param", action="append", nargs=2, metavar=("KEY", "VALUE"), help="Add a named parameter (can be used multiple times)")
    parser.add_argument("--pdf", help="Path to a PDF file to parse and query about (requires a template)")
    parser.add_argument("--pdf-range", help="Character range to extract from PDF (e.g., '0-1000')")
    parser.add_argument("--output-pdf", action="store_true", help="Output parsed PDF content with character positions")
    parser.add_argument("--estimate_cost", action="store_true", help="Estimate cost of query")

    args = parser.parse_args()

    if args.pdf and not (args.template or args.output_pdf):
        parser.error("The --pdf option requires either a template file (-t) or --output-pdf")

    client = ClaudeClient(args.template)

    params = dict(args.param) if args.param else {}
    
    if args.query and not args.template:
        params['query'] = args.query
            
    if args.pdf:
        pdf_content = ClaudeClient.parse_pdf(args.pdf, args.pdf_range)
        if pdf_content:
            if args.output_pdf:
                ClaudeClient.output_pdf_with_positions(pdf_content)
                return
            params['pdf_content'] = pdf_content
        else:
            sys.exit(1)

    if args.estimate_cost:
        query = client.build_query(**params)
        token_count = len(client.tokenizer.encode(query))
        response = client.query(**params)
        output_token_count = len(client.tokenizer.encode(response))
        cost = client.estimate_cost(query, token_count, output_token_count, client.tokenizer)
        print(f"Estimated cost: ${cost:.2f}")
        return

    if not args.template and 'query' not in params and not args.output_pdf:
        parser.error("When not using a template or --output-pdf, you must provide a query using -q or --query")

    if args.template and not args.pdf and not params:
        parser.error("When using a template, you must provide parameters with -p or use --pdf")

    if not args.output_pdf:
        response = client.query(**params)

        if args.json:
            parsed_json = client.parse_json(response)
            if parsed_json:
                print(json.dumps(parsed_json, indent=2))
            else:
                sys.exit(1)
        else:
            print(response)

if __name__ == "__main__":
    main()