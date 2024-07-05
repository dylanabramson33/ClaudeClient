from setuptools import setup, find_packages

setup(
    name="claude_client",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "jinja2",
        "anthropic",
    ],
    entry_points={
        "console_scripts": [
            "claude_client=claude_client:main",
        ],
    },
)