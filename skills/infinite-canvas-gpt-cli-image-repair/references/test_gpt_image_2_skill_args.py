import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main


class GPTImage2SkillArgTests(unittest.TestCase):
    def test_codex_config_model_reads_top_level_model_from_codex_home(self):
        with tempfile.TemporaryDirectory() as root:
            config = Path(root) / "config.toml"
            config.write_text('model = "config-host"\n[profiles.default]\nmodel = "nested-model"\n', encoding="utf-8")
            with patch.dict(os.environ, {"CODEX_HOME": root, "USERPROFILE": str(Path(root) / "profile")}, clear=False):
                self.assertEqual(main.codex_config_model(), "config-host")

    def test_codex_config_model_uses_userprofile_fallback_and_empty_on_parse_error(self):
        with tempfile.TemporaryDirectory() as root:
            config = Path(root) / ".codex" / "config.toml"
            config.parent.mkdir()
            config.write_text("model = 'userprofile-host'\n", encoding="utf-8")
            with patch.dict(os.environ, {"CODEX_HOME": "", "USERPROFILE": root}, clear=False):
                self.assertEqual(main.codex_config_model(), "userprofile-host")
            config.write_bytes(b"\xff")
            with patch.object(main.os.path, "expanduser", return_value=""), patch.dict(os.environ, {"CODEX_HOME": "", "USERPROFILE": root}, clear=False):
                self.assertEqual(main.codex_config_model(), "")

    def test_host_model_priority(self):
        with patch.object(main, "read_api_env_value", return_value=""), patch.object(main, "codex_config_model", return_value="config-host"), patch.dict(os.environ, {"CODEX_IMAGE_HOST_MODEL": "configured-image-host", "CODEX_MODEL": "generic-codex-model"}, clear=False):
            self.assertEqual(main.gpt_image_2_skill_model_arg("gpt-image-2", "codex"), "configured-image-host")

    def test_config_model_beats_image_ui_model(self):
        with patch.object(main, "read_api_env_value", return_value=""), patch.object(main, "codex_config_model", return_value="config-host"), patch.dict(os.environ, {"CODEX_IMAGE_HOST_MODEL": "", "CODEX_MODEL": ""}, clear=False):
            self.assertEqual(main.gpt_image_2_skill_model_arg("gpt-image-2", "codex"), "config-host")

    def test_openai_mapping_is_unchanged(self):
        self.assertEqual(main.gpt_image_2_skill_model_arg("", "openai"), "gpt-image-2")

    def test_codex_sizes(self):
        self.assertEqual(main.gpt_image_2_skill_size_arg("1024x1024", provider="codex"), "1024x1024")
        self.assertEqual(main.gpt_image_2_skill_size_arg("1600x900", provider="codex"), "1600x900")
        self.assertEqual(main.gpt_image_2_skill_size_arg("1K", provider="codex"), "auto")
        self.assertEqual(main.gpt_image_2_skill_size_arg("2K", provider="codex"), "2K")
        self.assertEqual(main.gpt_image_2_skill_size_arg("4K", provider="codex"), "4K")


if __name__ == "__main__":
    unittest.main()
