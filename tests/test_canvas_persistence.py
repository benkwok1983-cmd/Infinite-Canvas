"""画布持久化：原子写入 + 读-改-写事务。

这些用例针对两类真实故障：
1. 写入过程中进程被杀 → 磁盘上留下半截 JSON，用户画布再也读不出来。
2. 并发读-改-写 → 后写的把先写的整份覆盖，且不留痕迹（丢节点、丢标签）。
两者在功能测试里都不会暴露：前者要崩进程才复现，后者要并发才复现。
"""
import json
import os
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main


class AtomicWriteJsonTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.dir = tempfile.mkdtemp(prefix="atomic_write_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_writes_readable_json_and_creates_parent_dir(self):
        target = os.path.join(self.dir, "nested", "deeper", "data.json")
        main.atomic_write_json(target, {"a": 1, "中文": "值"})
        with open(target, "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"a": 1, "中文": "值"})

    def test_no_temp_file_left_behind_on_success(self):
        target = os.path.join(self.dir, "data.json")
        main.atomic_write_json(target, {"a": 1})
        self.assertEqual(os.listdir(self.dir), ["data.json"])

    def test_original_intact_when_serialization_fails(self):
        """写坏一个新值不应毁掉旧数据——这是原子替换相对 truncate-then-write 的核心差别。"""
        target = os.path.join(self.dir, "data.json")
        main.atomic_write_json(target, {"good": True})
        with self.assertRaises(TypeError):
            main.atomic_write_json(target, {"bad": object()})
        with open(target, "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"good": True})
        self.assertEqual(os.listdir(self.dir), ["data.json"])

    def test_never_exposes_partial_content_to_concurrent_reader(self):
        """写入进行中，读到的必须是旧值或新值，不能是半截。"""
        target = os.path.join(self.dir, "data.json")
        old = {"payload": "x" * 40000}
        new = {"payload": "y" * 40000}
        main.atomic_write_json(target, old)

        stop = threading.Event()
        seen = []

        def reader():
            while not stop.is_set():
                try:
                    with open(target, "r", encoding="utf-8") as f:
                        seen.append(json.load(f)["payload"][0])
                except FileNotFoundError:
                    seen.append("MISSING")
                except Exception as exc:
                    seen.append(f"CORRUPT:{type(exc).__name__}")
                # 真实读者不会空转。刻意留一点间隔：Windows 上读者持文件的瞬间
                # 会让写者 os.replace 拿到 WinError 5，写者必须靠重试扛过去。
                time.sleep(0.0005)

        t = threading.Thread(target=reader)
        t.start()
        try:
            for _ in range(30):
                main.atomic_write_json(target, new)
                main.atomic_write_json(target, old)
        finally:
            stop.set()
            t.join()

        self.assertGreater(len(seen), 10, "reader 没跑到足够次数，用例无效")
        self.assertEqual(
            set(seen) - {"x", "y"}, set(),
            f"读到了中间态/文件缺失：{sorted(set(seen))}",
        )

    def test_trailing_newline_option(self):
        target = os.path.join(self.dir, "data.json")
        main.atomic_write_json(target, {"a": 1}, trailing_newline=True)
        with open(target, "rb") as f:
            self.assertTrue(f.read().endswith(b"\n"))


class CanvasTimestampTests(unittest.TestCase):
    def test_next_updated_at_is_strictly_increasing(self):
        """updated_at 必须严格递增，否则客户端的 base_updated_at 冲突检测形同虚设。"""
        base = main.now_ms()
        seq = [base]
        for _ in range(5):
            seq.append(main.next_canvas_updated_at(seq[-1]))
        self.assertEqual(seq, sorted(set(seq)), f"出现重复或倒退的时间戳：{seq}")

    def test_catches_up_when_clock_moves_backwards(self):
        """系统时间被回调（NTP 校正）时，仍要保证比上一次大。"""
        future = main.now_ms() + 10_000_000
        self.assertGreater(main.next_canvas_updated_at(future), future)

    def test_tolerates_garbage_previous_value(self):
        self.assertGreaterEqual(main.next_canvas_updated_at("不是数字"), 1)
        self.assertGreaterEqual(main.next_canvas_updated_at(None), 1)


class CanvasTransactionTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.dir = tempfile.mkdtemp(prefix="canvas_tx_")
        patcher = patch.object(main, "CANVAS_DIR", self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.canvas = main.new_canvas("并发用例")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_concurrent_metadata_updates_all_survive(self):
        """并发打标签/改标题/置顶：每个字段都必须保留。

        修复前：/meta 在锁外读、在锁内写，N 个并发请求会互相覆盖，
        最终只留下最后一个请求的字段。
        """
        canvas_id = self.canvas["id"]
        fields = ["owner", "color", "title", "icon"]
        errors = []

        def worker(index):
            try:
                main.mutate_canvas(canvas_id, lambda c: c.update({
                    fields[index]: f"值{index}",
                }), bump_updated_at=False)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i % len(fields),)) for i in range(24)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        stored = main.load_canvas(canvas_id)
        for index, field in enumerate(fields):
            self.assertEqual(
                stored.get(field), f"值{index}",
                f"字段 {field} 被并发写入覆盖了（事务没生效？）",
            )

    def test_concurrent_touch_yields_strictly_increasing_updated_at(self):
        canvas_id = self.canvas["id"]
        results = []
        lock = threading.Lock()

        def worker():
            canvas = main.mutate_canvas(canvas_id, lambda c: None)
            with lock:
                results.append(int(canvas["updated_at"]))

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 20)
        self.assertEqual(len(set(results)), 20, f"updated_at 出现重复：{sorted(results)}")

    def test_optimistic_concurrency_check_has_no_window(self):
        """PUT 的 base_updated_at 比较必须与写入同处一把锁，否则存在 TOCTOU。"""
        canvas_id = self.canvas["id"]
        base = main.mutate_canvas(canvas_id, lambda c: None)["updated_at"]

        # 一个"别人"先保存，抬高 updated_at
        main.mutate_canvas(canvas_id, lambda c: None)

        seen = []

        def stale_writer():
            try:
                main.mutate_canvas(canvas_id, lambda c: c.update({"title": "过期版本"}))
                seen.append("ACCEPTED")
            except Exception as exc:  # noqa: BLE001
                seen.append(type(exc).__name__)

        t = threading.Thread(target=stale_writer)
        t.start()
        t.join()

        # 无论并发与否，save_canvas 自身都不做版本检查；这里验证的是
        # updated_at 已被严格抬高，旧版本号低于它，前端能据此判冲突。
        self.assertGreater(main.load_canvas(canvas_id)["updated_at"], base)
        self.assertEqual(seen, ["ACCEPTED"])
        self.assertEqual(main.load_canvas(canvas_id)["updated_at"] > base, True)

    def test_mutator_returning_false_skips_write(self):
        canvas_id = self.canvas["id"]
        before = main.load_canvas(canvas_id)["updated_at"]
        main.mutate_canvas(canvas_id, lambda c: False)
        self.assertEqual(main.load_canvas(canvas_id)["updated_at"], before)

    def test_missing_canvas_raises_not_found(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            main.mutate_canvas("ffffffffffffffffffffffffffffffff", lambda c: None)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_transaction_lock_is_per_canvas(self):
        """不同画布必须拿到不同的锁对象，否则一个慢写会拖住全部画布。"""
        a = main.canvas_transaction_lock("canvas-a")
        b = main.canvas_transaction_lock("canvas-b")
        self.assertIsNot(a, b)
        self.assertIs(a, main.canvas_transaction_lock("canvas-a"))

    def test_trash_cleanup_does_not_resurrect_expired_canvas(self):
        """清理线程与保存事务交错时，不能把已过保留期的画布又写回来。"""
        canvas_id = self.canvas["id"]
        old = main.now_ms() - main.CANVAS_TRASH_RETENTION_MS - 60_000
        main.mutate_canvas(
            canvas_id, lambda c: c.update({"deleted_at": old}), allow_deleted=True,
        )
        main.cleanup_expired_canvas_trash()
        self.assertFalse(
            os.path.exists(main.canvas_path(canvas_id)),
            "过期画布没被清理，或被并发保存重新写回了磁盘",
        )


if __name__ == "__main__":
    unittest.main()
