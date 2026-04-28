# Configuration file for the Sphinx documentation builder.
import os
import sys
import django

# Caminhos do projeto
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../../DQ4IAM_GOVERNANCE'))

# Config do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dq4iam_project.settings')
django.setup()

project = 'DQ4IAM_GOVERNANCE'
author = 'Sergio Santana dos Santos'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinxcontrib.plantuml',
    'sphinxcontrib.httpdomain',
]


plantuml = 'java -jar /home/sergio/plantuml.jar'
plantuml_output_format = 'svg'

templates_path = ['_templates']
exclude_patterns = []
language = 'pt-BR'

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
autoclass_content = 'both'


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
