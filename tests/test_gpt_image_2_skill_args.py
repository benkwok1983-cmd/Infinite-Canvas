import os
import sys
import json
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
            config.write_text(
                'model = "config-host"\n[profiles.default]\nmodel = "nested-model"\n',
                encoding="utf-8",
            )
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
            with patch.object(main.os.path, "expanduser", return_value=""), patch.dict(
                os.environ, {"CODEX_HOME": "", "USERPROFILE": root}, clear=False
            ):
                self.assertEqual(main.codex_config_model(), "")

    def test_codex_image_model_uses_configured_host_model(self):
        with patch.object(main, "read_api_env_value", return_value=""), patch.object(
            main, "codex_config_model", return_value="config-host"
        ), patch.dict(
            os.environ,
            {
                "CODEX_IMAGE_HOST_MODEL": "configured-image-host",
                "CODEX_MODEL": "generic-codex-model",
            },
            clear=False,
        ):
            self.assertEqual(
                main.gpt_image_2_skill_model_arg("gpt-image-2", "codex"),
                "configured-image-host",
            )

    def test_codex_image_model_falls_back_to_codex_chat_default(self):
        with patch.object(main, "read_api_env_value", return_value=""), patch.object(
            main, "codex_config_model", return_value=""
        ), patch.dict(
            os.environ,
            {"CODEX_IMAGE_HOST_MODEL": "", "CODEX_MODEL": ""},
            clear=False,
        ), patch.object(main, "CODEX_DEFAULT_CHAT_MODELS", ["configured-chat-default"]):
            self.assertEqual(
                main.gpt_image_2_skill_model_arg("$imagegen", "codex"),
                "configured-chat-default",
            )

    def test_codex_config_model_takes_precedence_over_image_ui_model(self):
        with patch.object(main, "read_api_env_value", return_value=""), patch.object(
            main, "codex_config_model", return_value="config-host"
        ), patch.dict(
            os.environ,
            {"CODEX_IMAGE_HOST_MODEL": "", "CODEX_MODEL": ""},
            clear=False,
        ):
            self.assertEqual(main.gpt_image_2_skill_model_arg("gpt-image-2", "codex"), "config-host")

    def test_openai_image_model_mapping_is_unchanged(self):
        self.assertEqual(main.gpt_image_2_skill_model_arg("", "openai"), "gpt-image-2")
        self.assertEqual(main.gpt_image_2_skill_model_arg("$imagegen", "openai"), "gpt-image-2")

    def test_codex_size_uses_explicit_small_dimensions(self):
        self.assertEqual(main.gpt_image_2_skill_size_arg("1024x1024", provider="codex"), "1024x1024")
        self.assertEqual(main.gpt_image_2_skill_size_arg("1600x900", provider="codex"), "1600x900")
        self.assertEqual(main.gpt_image_2_skill_size_arg("900x1600", provider="codex"), "900x1600")

    def test_codex_size_maps_fuzzy_one_k_to_auto(self):
        # 2026-09-19 实测：codex 通道 auto/2K/4K 触发 missing_image_result，收敛 1K
        self.assertEqual(main.gpt_image_2_skill_size_arg("1K", provider="codex"), "1K")
        self.assertEqual(main.gpt_image_2_skill_size_arg("", prompt="1024 output", provider="codex"), "1K")

    def test_codex_size_preserves_two_k_four_k_and_large_dimensions(self):
        # auto/2K/4K 档位值 → 1K；精确宽高 → snap 到 16 倍数的精确像素（实测仅此两类被服务端接受）
        self.assertEqual(main.gpt_image_2_skill_size_arg("2K", provider="codex"), "1K")
        self.assertEqual(main.gpt_image_2_skill_size_arg("4K", provider="codex"), "1K")
        self.assertEqual(main.gpt_image_2_skill_size_arg("2048x1365", provider="codex"), "2048x1376")
        self.assertEqual(main.gpt_image_2_skill_size_arg("3840x2160", provider="codex"), "3840x2160")


class CodexExperimentalImageModelTests(unittest.TestCase):
    def test_experimental_model_detection_is_case_insensitive_and_strict(self):
        self.assertEqual(main.codex_experimental_image_model("gpt-image-2.5-flare"), "gpt-image-2.5-flare")
        self.assertEqual(main.codex_experimental_image_model("GPT-Image-2.5-Sunburst "), "gpt-image-2.5-sunburst")
        self.assertEqual(main.codex_experimental_image_model("gpt-image-2"), "")
        self.assertEqual(main.codex_experimental_image_model(""), "")
        self.assertEqual(main.codex_experimental_image_model("gpt-image-2.5-fake"), "")
        self.assertEqual(main.codex_experimental_image_model("gpt-5.6-sol"), "")

    def test_request_body_injects_tool_model(self):
        body = main.codex_image_request_body("prompt text", "gpt-5.6-sol", "gpt-image-2.5-flare", "1024x1024")
        self.assertEqual(body["model"], "gpt-5.6-sol")
        self.assertEqual(body["tools"][0]["model"], "gpt-image-2.5-flare")
        self.assertEqual(body["tools"][0]["background"], "auto")
        self.assertEqual(body["tools"][0]["size"], "1024x1024")
        self.assertEqual(body["tools"][0]["type"], "image_generation")
        self.assertFalse(body["store"])

    def test_request_body_auto_omits_tool_model(self):
        body = main.codex_image_request_body("prompt text", "gpt-5.6-sol", "", "")
        self.assertNotIn("model", body["tools"][0])
        self.assertNotIn("size", body["tools"][0])
        self.assertEqual(body["tools"][0]["background"], "auto")

    def test_observed_model_parsed_from_event_stream(self):
        events = "\n".join(
            [
                json.dumps({"type": "response.created", "data": {"response": {"tools": [{"type": "image_generation", "model": "gpt-image-2-codex"}]}}}),
                json.dumps({"type": "response.completed", "response": {"tools": [{"type": "image_generation", "model": "gpt-image-2-codex"}]}}),
                "not-json-line",
            ]
        )
        self.assertEqual(main.parse_codex_observed_image_model(events), ["gpt-image-2-codex"])

    def test_observed_model_prefers_completed_over_created_echo(self):
        # response.created 回显请求值（实验性 2.5 名），completed 才是服务端最终路由
        events = "\n".join(
            [
                json.dumps({"type": "response.created", "response": {"tools": [{"type": "image_generation", "model": "gpt-image-2.5-flare"}]}}),
                json.dumps({"type": "response.completed", "response": {"tools": [{"type": "image_generation", "model": "gpt-image-2-codex"}]}}),
            ]
        )
        self.assertEqual(main.parse_codex_observed_image_model(events), ["gpt-image-2-codex"])

    def test_observed_model_parses_pretty_json_result_payload(self):
        payload = json.dumps({"type": "response.completed", "response": {"tools": [{"type": "image_generation", "model": "gpt-image-2-codex"}]}}, indent=2)
        self.assertEqual(main.parse_codex_observed_image_model(payload), ["gpt-image-2-codex"])

    def test_observed_model_empty_on_unrelated_events(self):
        self.assertEqual(main.parse_codex_observed_image_model('{"type":"progress","message":"waiting"}'), [])
        self.assertEqual(main.parse_codex_observed_image_model(""), [])
        self.assertEqual(main.parse_codex_observed_image_model("garbage"), [])

    def test_models_payload_exposes_experimental_tier(self):
        payload = main.codex_models_payload()
        self.assertIn("gpt-image-2", payload["image_models"])
        self.assertIn("gpt-image-2.5-flare", payload["experimental_image_models"])
        self.assertIn("gpt-image-2.5-sunburst", payload["experimental_image_models"])
        self.assertIn("gpt-image-2.5-flare", payload["all"])


class CodexImageRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_experimental_with_refs_rejected_before_any_execution(self):
        with tempfile.TemporaryDirectory() as root:
            ref = Path(root) / "ref.png"
            ref.write_bytes(b"png")
            with patch.object(main, "gpt_image_2_skill_executable", return_value="fake-exe"):
                with self.assertRaises(main.HTTPException) as ctx:
                    await main.generate_codex_provider_image_via_gpt_image_2_skill(
                        "prompt", "1024x1024", "", ref_paths=[str(ref)], image_model="gpt-image-2.5-flare"
                    )
            self.assertEqual(ctx.exception.status_code, 400)

    async def test_image_model_is_passed_through_to_skill_call(self):
        captured = {}

        async def fake_skill(prompt, size, model, ref_paths=None, image_model="", provider=None):
            captured["image_model"] = image_model
            captured["model"] = model
            captured["provider"] = provider
            return None

        with patch.object(main, "generate_codex_provider_image_via_gpt_image_2_skill", fake_skill):
            with self.assertRaises(main.HTTPException):
                await main.generate_codex_provider_image("prompt", "1024x1024", "gpt-image-2", reference_images=[], image_model="gpt-image-2.5-sunburst")
        self.assertEqual(captured["image_model"], "gpt-image-2.5-sunburst")


class CodexApiFallbackTests(unittest.TestCase):
    def _attempts(self, provider_cfg, auth_data):
        with patch.object(main, "gpt_image_2_skill_auth_json", return_value=auth_data), patch.object(
            main, "gpt_image_2_skill_provider_args", return_value=(["--provider", "codex"], "codex")
        ), patch.object(main, "gpt_image_2_skill_api_key", return_value=str(auth_data.get("OPENAI_API_KEY") or "")):
            return main.codex_image_skill_attempts(provider_cfg, "auth.json")

    def test_fallback_disabled_by_default_even_with_key(self):
        attempts = self._attempts({"id": "codex", "protocol": "codex"}, {"tokens": {}, "OPENAI_API_KEY": "sk-test"})
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0][1], "codex")

    def test_fallback_enabled_by_switch_adds_openai_attempt(self):
        attempts = self._attempts(
            {"id": "codex", "protocol": "codex", "allow_api_fallback": True},
            {"tokens": {}, "OPENAI_API_KEY": "sk-test"},
        )
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0][1], "codex")
        self.assertEqual(attempts[1][1], "openai")
        self.assertIn("--api-key", attempts[1][0])
        self.assertIn("sk-test", attempts[1][0])

    def test_fallback_switch_on_without_key_stays_single_attempt(self):
        attempts = self._attempts({"id": "codex", "protocol": "codex", "allow_api_fallback": True}, {"tokens": {}})
        self.assertEqual(len(attempts), 1)

    def test_fallback_requires_codex_provider_resolution(self):
        with patch.object(main, "gpt_image_2_skill_auth_json", return_value={"OPENAI_API_KEY": "sk-test"}), patch.object(
            main, "gpt_image_2_skill_provider_args", return_value=(["--provider", "openai", "--api-key", "sk-test"], "openai")
        ), patch.object(main, "gpt_image_2_skill_api_key", return_value="sk-test"):
            attempts = main.codex_image_skill_attempts({"allow_api_fallback": True}, "auth.json")
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0][1], "openai")


if __name__ == "__main__":
    unittest.main()
