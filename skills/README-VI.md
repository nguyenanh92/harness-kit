# Hướng dẫn dùng Harness Kit (Tiếng Việt)

Tài liệu này hướng dẫn cách scaffold, audit và chạy thử bộ harness Python chỉ-dùng-thư-viện-chuẩn cho các AI coding agent (Claude Code, Cursor, Codex, Windsurf, Antigravity).

---

## 1. Yêu cầu

- **Python 3.8+** (dùng `py` trên Windows, `python3` ở nơi khác).
- **Không cần `pip install`** — toàn bộ kit chỉ dùng thư viện chuẩn Python.
- Hệ điều hành: Windows / macOS / Linux đều chạy được.

## 2. Cài đặt skill

Clone repo hoặc vendor làm submodule:

```bash
git clone https://github.com/nguyenanh92/harness-kit.git
# hoặc copy thư mục skills/ vào skill path của bạn
```

Mọi thứ chạy trực tiếp từ `skills/` — không cần `pip install` hay `npm install`.

## 3. Scaffold một harness mới

Lệnh tạo đầy đủ governance file ở thư mục gốc và 7 module Python trong `harness/`:

```bash
# Windows
py skills/scripts/scaffold_harness.py --target D:/path/to/project

# macOS / Linux
python3 skills/scripts/scaffold_harness.py --target /path/to/project
```

Tham số:

- `--harness-dir harness` — đổi tên thư mục chứa code (mặc định `harness`).
- `--agent-file CLAUDE.md` — tạo `CLAUDE.md` thay vì `AGENTS.md`.
- `--governance-only` — chỉ tạo file governance, không scaffold code.
- `--force` — ghi đè file đã có (xác nhận trước).

Sau khi chạy, project có:

```
project-root/
├── AGENTS.md                  # contract của agent
├── feature_list.json          # feature + dependencies
├── feature-list.schema.json   # schema để IDE auto-check
├── progress.md                # nhật ký phiên hiện tại
├── session-handoff.md         # bàn giao cho phiên kế tiếp
├── init.sh / init.ps1         # script verify fail-fast
└── harness/
    ├── harness.py             # vòng lặp orchestrator
    ├── context_manager.py     # compaction
    ├── tool_registry.py       # quyền + classify_command
    ├── persistence.py         # JSONL session log
    ├── hooks.py               # pre/post-tool hook + trust gate
    ├── subagent.py            # fork đơn cấp
    ├── prompt_assembly.py     # lắp prompt giữ prefix cache
    └── __init__.py
```

## 4. Validate / chấm điểm harness

```bash
# Text report
py skills/scripts/validate_harness.py --target D:/path/to/project

# JSON cho CI
py skills/scripts/validate_harness.py --target D:/path/to/project --json

# HTML self-contained
py skills/scripts/validate_harness.py --target D:/path/to/project --html report.html

# Fail CI khi điểm dưới ngưỡng
py skills/scripts/validate_harness.py --target D:/path/to/project --min-score 80
```

Bộ chấm cho điểm trên 5 subsystem (Instructions / State / Verification / Scope / Lifecycle), mỗi subsystem 5 check, tổng điểm thang 100. Điểm thấp nhất là `bottleneck` — gợi ý ưu tiên cải thiện.

> Điểm là *cấu trúc*, không phải hiệu quả thực tế. Vẫn cần chạy agent trên task thật trước/sau để xác nhận.

## 5. Benchmark + báo cáo HTML

```bash
py skills/scripts/run_benchmark.py --target D:/path/to/project --html bench.html
```

Kết hợp điểm cấu trúc với độ phủ eval (`evals/evals.json`), kèm khuyến nghị.

## 6. Chạy giả lập (Mock Mode)

Sau khi scaffold, từ trong project đích chạy:

```bash
# Windows
py harness/harness.py --mock --goal "Tạo một lớp Calculator đơn giản"

# macOS / Linux
python3 harness/harness.py --mock --goal "Tạo một lớp Calculator đơn giản"
```

Lượt giả lập:

1. **Iteration 1** — LLM gọi `spawn_subagent` để kiểm tra cấu trúc thư mục; hook chạy, sub-agent cô lập, trả kết quả.
2. **Iteration 2** — LLM gọi `write_file` để tạo `calculator.py`.
3. **Iteration 3** — LLM gọi `run_shell` để `py_compile`; `classify_command` phân loại WORKSPACE_WRITE và cho phép.
4. **Iteration 4** — Loop hoàn tất, đánh dấu done.

Sau lần chạy đầu, thư mục `.harness/` xuất hiện với `*.jsonl` log. Nếu crash giữa chừng, chạy lại sẽ replay JSONL để khôi phục context.

Dọn dẹp:

```powershell
# Windows
Remove-Item calculator.py -Force -ErrorAction SilentlyContinue
Remove-Item .harness -Recurse -Force -ErrorAction SilentlyContinue
```

```bash
# macOS / Linux
rm -f calculator.py
rm -rf .harness
```

## 7. Tích hợp Live Mode (gọi LLM thật)

Override một method duy nhất:

```python
from harness.harness import Harness

class LiveHarness(Harness):
    def _model_turn(self, messages):
        # gọi Anthropic / OpenAI ở đây
        return {"role": "assistant", "content": ..., "tool_call": ...}
```

Mọi cơ chế khác — compaction, permission gate, JSONL log, hook trust — vẫn chạy nguyên. Giữ adapter LLM trong code của caller, không đẩy vào module harness để harness vẫn zero-dependency.

## 8. Khi nào đọc reference nào

| Bài toán                                         | Reference |
|--------------------------------------------------|-----------|
| Invariant tổng (zero-dep, bounded loop, JSONL)   | `references/architecture-principles.md` |
| 9 module làm gì, mở rộng ở đâu                   | `references/nine-components.vi.md` |
| Phân quyền, classify_command, fork sub-agent     | `references/tool-registry-and-safety.md` |
| Compaction, prefix cache, JSONL replay           | `references/context-and-memory.md` |
| Bootstrap, hook trust, restart                   | `references/lifecycle-and-hooks.md` |
| Các kiểu lỗi phi-hiển-nhiên (đánh số)            | `references/gotchas.md` |
