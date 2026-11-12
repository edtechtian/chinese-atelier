"""Regression for a completion-blocking frontend error missed by API tests."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')
if not NODE:
    bundled = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    NODE = str(bundled) if bundled.is_file() else None


class FrontendRenderTests(unittest.TestCase):
    @unittest.skipUnless(NODE, 'Node is needed for the JavaScript network regression test')
    def test_visual_renderers(self):
        result = subprocess.run([NODE, str(ROOT / 'tests/frontend_visual.mjs')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_network_failure_guidance(self):
        result = subprocess.run([NODE, str(ROOT / 'tests/frontend_network.mjs')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('actionable guidance', result.stdout)

    @unittest.skipUnless(NODE, 'Node is needed for the microlearning rendering regression')
    def test_all_100_microsteps_render(self):
        result = subprocess.run([NODE, str(ROOT / 'tests/frontend_daily.mjs')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('all 100 steps', result.stdout)

    @unittest.skipUnless(NODE, 'Node is needed for the JavaScript renderer regression test')
    def test_all_twenty_reflection_pages_render(self):
        result = subprocess.run([NODE, str(ROOT / 'tests/frontend_render.mjs')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('all 20 lessons', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
