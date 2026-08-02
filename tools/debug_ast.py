import ast
p='ui/video_news_page.py'
s=open(p,encoding='utf-8').read()
t=ast.parse(s)
for node in ast.walk(t):
    if isinstance(node, ast.Import):
        print('IMPORT', [a.name for a in node.names])
    if isinstance(node, ast.ImportFrom):
        print('IMPORTFROM', node.module, 'level', getattr(node,'level',0))
print('done')
