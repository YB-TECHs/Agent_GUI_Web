import urllib.request
import urllib.parse
import re

def search_ddg(query):
    url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64 AppleWebKit/537.36)'})
    try:
        html_content = urllib.request.urlopen(req).read().decode('utf-8')
        links = re.findall(r'href="//duckduckgo.com/l/\?uddg=([^"]+)"', html_content)
        clean = []
        for link in links:
            actual = urllib.parse.unquote(link.split('&')[0])
            if actual.lower().endswith('.pdf') or 'pdf' in actual.lower():
                clean.append(actual)
        return clean[:2]
    except Exception as e:
        return [str(e)]

print('--- STRATEGIE MINFI ---')
for l in search_ddg('Stratégie Nationale de la Finance Inclusive Cameroun filetype:pdf'): print(l)

print('\n--- TARIFICATION CNC ---')
for l in search_ddg('tarification des services financiers au Cameroun CNC filetype:pdf'): print(l)

print('\n--- TONTINES ---')
for l in search_ddg('La tontine au Cameroun filetype:pdf'): print(l)
