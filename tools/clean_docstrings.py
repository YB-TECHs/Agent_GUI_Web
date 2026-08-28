import os
import re

def clean_docstrings(filepath):
    encodings = ['utf-8', 'utf-8-sig', 'cp1252']
    content = None
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            best_enc = enc
            break
        except UnicodeDecodeError:
            continue
            
    if not content: return

    original = content
    filename = os.path.basename(filepath)

    # 1. Raser les docstrings de module trop verbeuses au debut du fichier
    def repl(m):
        return f'"""\nModule {filename}.\n"""'
    
    content = re.sub(r'^\s*\"\"\"[\s\S]*?\"\"\"', repl, content)
    
    # 2. Remplacer les mots trop "corporate IA" partout dans le code
    content = re.sub(r'(?i)erreurs', 'erreurs', content)
    content = re.sub(r'(?i)erreurs', 'erreurs', content)
    content = re.sub(r'(?i)erreur', 'erreur', content)
    content = re.sub(r'(?i)tests', 'tests', content)
    content = re.sub(r'(?i)stats', 'stats', content)
    content = re.sub(r'(?i)stats', 'stats', content)
    
    if content != original:
        with open(filepath, 'w', encoding=best_enc) as f:
            f.write(content)
        print(f'Docstring nettoyee : {filepath}')

for root, dirs, files in os.walk('.'):
    if '.git' in root or '__pycache__' in root or '.vscode' in root or '.streamlit' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            clean_docstrings(os.path.join(root, file))

print('Nettoyage agressif des en-tetes termine.')
