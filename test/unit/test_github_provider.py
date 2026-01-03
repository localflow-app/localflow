
import unittest
import shutil
from pathlib import Path
from src.core.providers.github_provider import GitHubNodeProvider
from src.core.node_registry import NodeSource, get_registry

class TestGitHubProvider(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("user_data_test")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.provider = GitHubNodeProvider(self.tmp_dir)
        self.registry = get_registry()
        # Override user_data_dir for test
        self.registry._user_data_dir = self.tmp_dir

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_parse_url(self):
        cases = [
            ("https://github.com/owner/repo", ("owner", "repo")),
            ("owner/repo", ("owner", "repo")),
            ("https://github.com/owner/repo.git", ("owner", "repo")),
            ("invalid-url", None),
        ]
        for url, expected in cases:
            with self.subTest(url=url):
                result = self.provider.parse_url(url)
                self.assertEqual(result, expected)

    def test_download_and_delete_node(self):
        url = "https://github.com/test_owner/test_repo"
        
        # Test Download
        node_def = self.provider.download_node(url)
        self.assertIsNotNone(node_def)
        self.assertEqual(node_def.source, NodeSource.GITHUB)
        self.assertEqual(node_def.repo_url, url)
        
        # Check files created
        node_path = self.tmp_dir / "external_nodes" / "github" / "test_owner" / "test_repo"
        self.assertTrue((node_path / "node.json").exists())
        self.assertTrue((node_path / "node.py").exists())
        
        # Check Registration
        self.assertIn(node_def.node_type, self.registry._nodes)
        
        # Test Delete
        success = self.provider.delete_node(node_def.node_type)
        self.assertTrue(success)
        self.assertFalse(node_path.exists())
        self.assertNotIn(node_def.node_type, self.registry._nodes)

if __name__ == '__main__':
    unittest.main()
