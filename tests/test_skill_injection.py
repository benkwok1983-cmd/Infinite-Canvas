import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main


def make_skill(root, name="style-a", body="Use watercolor style with soft edges."):
    path = os.path.join(root, name)
    os.makedirs(path, exist_ok=True)
    (Path(path) / "SKILL.md").write_text(f"---\nname: {name}\nversion: 1.0\n---\n\n{body}\n", encoding="utf-8")
    return path


class SkillInjectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.custom_dir = os.path.join(self.tmp.name, "custom")
        os.makedirs(self.custom_dir)
        self._patchers = [
            patch.object(main, "SKILLS_CUSTOM_DIR", self.custom_dir),
            patch.object(main, "SKILL_COMPILE_CACHE_FILE", os.path.join(self.tmp.name, "cache.json")),
        ]
        for p in self._patchers:
            p.start()
        make_skill(self.custom_dir, "style-a", "Watercolor style, soft edges.")
        make_skill(self.custom_dir, "style-b", "Cyberpunk neon, high contrast.")

    def tearDown(self):
        for p in self._patchers:
            p.stop()
        self.tmp.cleanup()

    def test_fast_compile_truncates_to_upstream_limit(self):
        async def run():
            result = await main.compile_skill_prompt(main.SkillSelection(source="custom", id="style-a", mode="fast"), "short prompt")
            return result["compiled_prompt"]
        compiled = self._run(run())
        self.assertLessEqual(len(compiled), main.SKILL_FAST_PROMPT_MAX + 50)

    def test_fast_compile_composes_body_and_prompt(self):
        async def run():
            result = await main.compile_skill_prompt(main.SkillSelection(source="custom", id="style-a", mode="fast"), "a cat on a windowsill")
            return result
        result = self._run(run())
        self.assertIn("Watercolor style, soft edges.", result["compiled_prompt"])
        self.assertIn("a cat on a windowsill", result["compiled_prompt"])
        self.assertEqual(result["skill_used"]["id"], "style-a")
        self.assertEqual(result["skill_used"]["mode"], "fast")
        self.assertTrue(result["skill_used"]["sha"])

    def test_different_skills_produce_different_prompts(self):
        async def run():
            a = await main.compile_skill_prompt(main.SkillSelection(source="custom", id="style-a", mode="fast"), "same prompt")
            b = await main.compile_skill_prompt(main.SkillSelection(source="custom", id="style-b", mode="fast"), "same prompt")
            return a["compiled_prompt"], b["compiled_prompt"]
        prompt_a, prompt_b = self._run(run())
        self.assertNotEqual(prompt_a, prompt_b)

    def test_llm_mode_uses_cache_on_second_call(self):
        calls = {"n": 0}

        async def fake_canvas_llm(payload):
            calls["n"] += 1
            return {"text": f"compiled #{calls['n']}", "model": "fake", "raw_usage": None}

        async def run():
            with patch.object(main, "canvas_llm", fake_canvas_llm):
                with patch.object(main, "get_primary_provider_id", return_value="comfly"):
                    first = await main.compile_skill_prompt(main.SkillSelection(source="custom", id="style-a", mode="llm"), "same prompt")
                    second = await main.compile_skill_prompt(main.SkillSelection(source="custom", id="style-a", mode="llm"), "same prompt")
            return first, second
        first, second = self._run(run())
        self.assertEqual(calls["n"], 1)
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertEqual(first["compiled_prompt"], second["compiled_prompt"])

    def test_llm_mode_cache_invalidated_after_skill_edit(self):
        calls = {"n": 0}

        async def fake_canvas_llm(payload):
            calls["n"] += 1
            return {"text": f"compiled #{calls['n']}", "model": "fake", "raw_usage": None}

        async def run():
            with patch.object(main, "canvas_llm", fake_canvas_llm), patch.object(main, "get_primary_provider_id", return_value="comfly"):
                await main.compile_skill_prompt(main.SkillSelection(source="custom", id="style-a", mode="llm"), "same prompt")
                (Path(self.custom_dir) / "style-a" / "SKILL.md").write_text(
                    "---\nname: style-a\nversion: 1.1\n---\n\nEdited body.\n", encoding="utf-8")
                await main.compile_skill_prompt(main.SkillSelection(source="custom", id="style-a", mode="llm"), "same prompt")
        self._run(run())
        self.assertEqual(calls["n"], 2)

    def test_build_online_image_result_injects_compiled_prompt(self):
        captured = {}

        async def fake_generate_ai_image(prompt, size, quality, model, refs, provider_id, aspect_ratio="", resolution="", image_model=""):
            captured["prompt"] = prompt
            return {"type": "url", "value": "/output/fake.png"}, {"images": ["/output/fake.png"]}

        async def run():
            payload = main.OnlineImageRequest(
                prompt="a cat", provider_id="comfly", size="1024x1024",
                skill=main.SkillSelection(source="custom", id="style-a", mode="fast"),
            )
            with patch.object(main, "get_api_provider", return_value={"id": "comfly", "image_models": ["m1"], "name": "Comfly"}), \
                 patch.object(main, "generate_ai_image", fake_generate_ai_image), \
                 patch.object(main, "save_to_history", lambda result: None), \
                 patch.object(main, "snap_size_to_multiple", side_effect=lambda size, step: size), \
                 patch.object(main, "GLOBAL_LOOP", None):
                result = await main.build_online_image_result(payload)
            return result
        result = self._run(run())
        self.assertIn("Watercolor style, soft edges.", captured["prompt"])
        self.assertEqual(result["prompt"], "a cat")
        self.assertEqual(result["skill_used"]["id"], "style-a")
        self.assertIn("Watercolor style, soft edges.", result["compiled_prompt"])

    def test_build_online_image_result_without_skill_is_unchanged(self):
        captured = {}

        async def fake_generate_ai_image(prompt, size, quality, model, refs, provider_id, aspect_ratio="", resolution="", image_model=""):
            captured["prompt"] = prompt
            return {"type": "url", "value": "/output/fake.png"}, {"images": ["/output/fake.png"]}

        async def run():
            payload = main.OnlineImageRequest(prompt="plain prompt", provider_id="comfly", size="1024x1024")
            with patch.object(main, "get_api_provider", return_value={"id": "comfly", "image_models": ["m1"], "name": "Comfly"}), \
                 patch.object(main, "generate_ai_image", fake_generate_ai_image), \
                 patch.object(main, "save_to_history", lambda result: None), \
                 patch.object(main, "snap_size_to_multiple", side_effect=lambda size, step: size), \
                 patch.object(main, "GLOBAL_LOOP", None):
                result = await main.build_online_image_result(payload)
            return result
        result = self._run(run())
        self.assertEqual(captured["prompt"], "plain prompt")
        self.assertNotIn("skill_used", result)
        self.assertNotIn("compiled_prompt", result)

    def _run(self, coro):
        import asyncio
        return asyncio.run(coro)


if __name__ == "__main__":
    unittest.main()
