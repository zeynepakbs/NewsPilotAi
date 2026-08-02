import ast
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def all_py_files(root):
    ignores = {'.venv', 'venv', 'env', '__pycache__'}
    files = []
    for p in root.rglob('*.py'):
        parts = set(p.parts)
        if parts & ignores:
            continue
        files.append(p)
    return files

def module_name_from_path(path, root):
    rel = path.relative_to(root).as_posix()
    if rel.endswith('__init__.py'):
        return rel[: -len('/__init__.py')].replace('/', '.')
    return rel[:-3].replace('/', '.')

def main():
    files = all_py_files(ROOT)

    module_to_path = {}
    path_to_module = {}
    for p in files:
        mod = module_name_from_path(p, ROOT)
        module_to_path[mod] = p
        path_to_module[p] = mod

    # parse imports
    edges = {p: set() for p in files}
    imported_by = {p: set() for p in files}

    for p in files:
        try:
            src = p.read_text(encoding='utf-8')
        except Exception:
            src = ''
        try:
            tree = ast.parse(src)
        except Exception:
            continue

        mymod = path_to_module[p]
        pkg_parts = mymod.split('.')

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                if node.level and node.level > 0:
                    # resolve relative import
                    base_parts = pkg_parts[:-node.level]
                    if module:
                        name = '.'.join(base_parts + [module])
                    else:
                        name = '.'.join(base_parts)
                    targets = [name]
                else:
                    if module:
                        targets = [module]
                    else:
                        targets = []
            else:
                continue

            # debug: if this is ui/video_news_page.py, print import nodes
            if p == ROOT / 'ui' / 'video_news_page.py':
                for node2 in ast.walk(tree):
                    if isinstance(node2, ast.Import):
                        print('# AST Import in video_news_page:', [a.name for a in node2.names])
                    if isinstance(node2, ast.ImportFrom):
                        print('# AST ImportFrom in video_news_page:', node2.module, 'level', node2.level)

            for target in targets:
                # try exact match
                if target in module_to_path:
                    tgt_path = module_to_path[target]
                    edges[p].add(tgt_path)
                    imported_by[tgt_path].add(p)
                    # mark parent packages' __init__.py as imported if present
                    parts = target.split('.')
                    for i in range(1, len(parts)):
                        pkg = '.'.join(parts[:i])
                        if pkg in module_to_path:
                            pkg_path = module_to_path[pkg]
                            imported_by[pkg_path].add(p)
                else:
                    # try progressively shorter suffixes
                    parts = target.split('.')
                    for i in range(len(parts), 0, -1):
                        candidate = '.'.join(parts[:i])
                        if candidate in module_to_path:
                            tgt_path = module_to_path[candidate]
                            edges[p].add(tgt_path)
                            imported_by[tgt_path].add(p)
                            break

    # find entry point
    entry = ROOT / 'app.py'
    reachable = set()
    if entry.exists():
        stack = [entry]
        while stack:
            cur = stack.pop()
            if cur in reachable:
                continue
            reachable.add(cur)
            for nb in edges.get(cur, []):
                stack.append(nb)

    # classify
    unimported = [p for p in files if len(imported_by.get(p, [])) == 0]

    safe_delete = []
    probably_unused = []
    used = []

    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        if p in reachable:
            used.append((rel, 'reachable from app.py'))
        else:
            if p in unimported:
                # test files or backup
                name = p.name.lower()
                if name.startswith('test_') or name.endswith('.bak') or 'backup' in name or 'old' in name:
                    probably_unused.append((rel, 'no imports; test/backup-like file'))
                else:
                    safe_delete.append((rel, 'no imports; not a test/backup'))
            else:
                # imported somewhere but not reachable from app.py
                probably_unused.append((rel, 'imported but not reachable from app.py'))

    # print report
    # debug: show edges for ui/video_news_page.py if present
    probe = ROOT / 'ui' / 'video_news_page.py'
    if probe in edges:
        print(f'# DEBUG edges from {probe.relative_to(ROOT)} ->')
        for nb in edges[probe]:
            print('  -', nb.relative_to(ROOT))
        print('\n')
    print('## Güvenle Silinebilir')
    for p,reason in sorted(safe_delete):
        print(f'- {p}')
        print(f'  - {reason}')

    print('\n## Muhtemelen Kullanılmıyor')
    for p,reason in sorted(probably_unused):
        print(f'- {p}')
        print(f'  - {reason}')

    print('\n## Kullanılıyor')
    for p,reason in sorted(used):
        print(f'- {p}')
        print(f'  - {reason}')

if __name__ == "__main__":
    main()
