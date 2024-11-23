#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from collections import defaultdict
import tempfile
import unittest

def parse_arguments():
    parser = argparse.ArgumentParser(description='Визуализация графа зависимостей git-репозитория.')
    parser.add_argument('--graphviz', required=True, help='Путь к программе для визуализации графов (dot).')
    parser.add_argument('--repo', required=True, help='Путь к анализируемому репозиторию.')
    parser.add_argument('--file-hash', required=True, help='Хеш-значение файла в репозитории.')
    return parser.parse_args()

def get_commits_with_file(repo_path, file_hash):
    """Получает список коммитов, содержащих файл с заданным хеш-значением."""
    try:
        git_cmd = ['git', '-C', repo_path, 'rev-list', '--all']
        commits = subprocess.check_output(git_cmd).decode().splitlines()
        matching_commits = []
        for commit in commits:
            git_ls_cmd = ['git', '-C', repo_path, 'ls-tree', '-r', commit]
            tree_objects = subprocess.check_output(git_ls_cmd).decode().splitlines()
            for obj in tree_objects:
                mode, type_, hash_, path = obj.strip().split(None, 3)
                if hash_ == file_hash:
                    matching_commits.append(commit)
                    break
        return matching_commits
    except subprocess.CalledProcessError as e:
        print(f'Ошибка при выполнении git-команды: {e}', file=sys.stderr)
        sys.exit(1)

def build_dependency_graph(repo_path, commits):
    """Строит граф зависимостей для указанных коммитов."""
    graph = defaultdict(set)
    for commit in commits:
        git_ls_cmd = ['git', '-C', repo_path, 'ls-tree', '-r', commit]
        tree_objects = subprocess.check_output(git_ls_cmd).decode().splitlines()
        for obj in tree_objects:
            mode, type_, hash_, path = obj.strip().split(None, 3)
            dirs = path.split('/')[:-1]
            for i in range(len(dirs)):
                parent = '/'.join(dirs[:i]) if i > 0 else '.'
                child = '/'.join(dirs[:i+1])
                graph[parent].add(child)
            if dirs:
                parent = '/'.join(dirs)
            else:
                parent = '.'
            graph[parent].add(path)
    return graph

def generate_dot(graph):
    """Генерирует описание графа в формате DOT."""
    dot = 'digraph dependencies {\n'
    for parent, children in graph.items():
        for child in children:
            dot += f'    "{parent}" -> "{child}";\n'
    dot += '}'
    return dot

def visualize_graph(dot_content, graphviz_path):
    """Визуализирует граф с помощью Graphviz."""
    with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.dot') as dot_file:
        dot_file.write(dot_content)
        dot_file_name = dot_file.name
    output_file = dot_file_name + '.png'
    try:
        subprocess.run([graphviz_path, '-Tpng', dot_file_name, '-o', output_file], check=True)
        if sys.platform == 'darwin':
            subprocess.run(['open', output_file])
        elif sys.platform == 'linux':
            subprocess.run(['xdg-open', output_file])
        elif sys.platform == 'win32':
            os.startfile(output_file)
        else:
            print(f'Граф сохранен в файле {output_file}')
    except subprocess.CalledProcessError as e:
        print(f'Ошибка при визуализации графа: {e}', file=sys.stderr)
    finally:
        os.unlink(dot_file_name)

def main():
    args = parse_arguments()
    commits = get_commits_with_file(args.repo, args.file_hash)
    if not commits:
        print('Коммиты с заданным файлом не найдены.')
        sys.exit(0)
    graph = build_dependency_graph(args.repo, commits)
    dot_content = generate_dot(graph)
    visualize_graph(dot_content, args.graphviz)

if __name__ == '__main__':
    main()
