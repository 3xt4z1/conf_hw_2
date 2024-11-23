import unittest
from unittest.mock import patch, MagicMock
from dependency_visualizer import get_commits_with_file, generate_dot


class TestDependencyVisualizer(unittest.TestCase):

    @patch('subprocess.check_output')
    def test_get_commits_with_file(self, mock_check_output):
        mock_check_output.side_effect = [
            b'commit1\ncommit2\ncommit3',  # Вывод git rev-list
            b'100644 blob hash1\tfile1\n100644 blob hash2\tfile2',  # Вывод git ls-tree для commit1
            b'100644 blob hash3\tfile3\n100644 blob hash4\tfile4',  # Вывод git ls-tree для commit2
            b'100644 blob hash1\tfile1\n100644 blob hash5\tfile5',  # Вывод git ls-tree для commit3
        ]
        repo_path = '/path/to/repo'
        file_hash = 'hash1'
        commits = get_commits_with_file(repo_path, file_hash)
        self.assertEqual(commits, ['commit1', 'commit3'])

    def test_generate_dot(self):
        graph = {
            '.': {'src', 'README.md'},
            'src': {'src/main.py', 'src/utils.py'},
        }
        dot = generate_dot(graph)
        expected_dot = (
            'digraph dependencies {\n'
            '    "." -> "README.md";\n'
            '    "." -> "src";\n'
            '    "src" -> "src/main.py";\n'
            '    "src" -> "src/utils.py";\n'
            '}'
        )
        self.assertEqual(dot.strip(), expected_dot.strip())

if __name__ == '__main__':
    unittest.main()
