---
name: infinite-canvas-gpt-cli-image-repair
description: Repair the Infinite Canvas GPT CLI image path when it hardcodes an unsupported Codex host model or passes an unsupported 1K image size. Use for the known gpt-image-2-skill compatibility failure; do not use to add image providers or API billing.
---

# Infinite Canvas GPT CLI image repair

Use this skill only for an Infinite Canvas installation whose GPT CLI image generation fails with either of these known conditions:

- `gpt-image-2-skill` reports that `gpt-5.4` is unsupported for a ChatGPT account.
- `gpt-image-2-skill` rejects `--size 1K`.

## Scope

The repair changes only `main.py` and optionally adds the focused regression test. It does not edit `API/.env`, copy login credentials, add OpenAI API keys, install image providers, or integrate GPT Image 2.5.

The intended outcome is:

- Codex host model is resolved in this order: `CODEX_IMAGE_HOST_MODEL`, `CODEX_MODEL`, the user's Codex `config.toml`, a non-image UI model, then the project's chat-model fallback.
- `gpt-image-*` UI values are never sent as the Codex host model.
- Explicit small dimensions such as `1024x1024` are passed as dimensions; an ambiguous `1K` request becomes `auto`.

## Before changing files

1. Work in the target Infinite Canvas directory. Do not overwrite its entire `main.py`.
2. Check that `main.py` contains the old `return "gpt-5.4"` branch and/or returns `"1K"` in the Codex size branch. If neither is present, stop: this patch is not for that version.
3. Confirm `gpt-image-2-skill --version` and `codex --version` are available. Do not log in again automatically.
4. Read [the patch](references/repair.patch) and apply it with a patch tool. If its context does not apply cleanly, make only the equivalent changes at the matching functions; do not force a whole-file replacement.
5. Add [the focused test](references/test_gpt_image_2_skill_args.py) under `tests/` if the repository permits new tests.

## Verify without spending image quota

Run:

```powershell
& .\python\python.exe .\tests\test_gpt_image_2_skill_args.py -v
```

Then verify the active Codex model is discovered without exposing credentials:

```powershell
& .\python\python.exe -c "import sys; sys.path.insert(0,'.'); import main; print(main.codex_config_model()); print(main.gpt_image_2_skill_model_arg('gpt-image-2','codex')); print(main.gpt_image_2_skill_size_arg('1024x1024',provider='codex'))"
```

Expected output includes a supported host model, `1024x1024`, and never `gpt-5.4` or `1K` for the affected Codex path. Restart the Infinite Canvas server after the patch is verified.

## Stop conditions

Do not generate a test image unless the user explicitly authorizes a quota-consuming end-to-end check. Do not apply this patch if the target app uses a different helper CLI or has already replaced these functions with a newer compatibility layer.
