# Chín Thành phần Cốt lõi

Đọc tài liệu này khi bạn cần biết mỗi module template phục vụ mục đích gì, hoặc khi quyết định một tính năng mới thuộc về đâu.

## "Harness" ở đây nghĩa là gì

```
LLM  +  Harness  =  Agent
```

LLM cung cấp khả năng suy luận. Harness cung cấp vòng lặp, bộ nhớ, công cụ và các rào chắn an toàn. Bỏ một trong hai phía thì không còn là agent.

Một **framework** (LangChain, LangGraph, AutoGen) cố gắng đảm nhận cả hai. Một **harness** giữ mình nhỏ gọn: nó là lớp vỏ mỏng nhất mà LLM cần để làm việc hữu ích — bạn sở hữu nó, đọc hết từ đầu đến cuối được. Skill này ship một harness, không phải framework.

## Chín thành phần

| # | Thành phần              | Module                  | Trách nhiệm |
|---|-------------------------|-------------------------|-------------|
| 1 | Vòng lặp while          | `harness.py`            | Điều phối có giới hạn; kết nối tám thành phần còn lại |
| 2 | Nén ngữ cảnh            | `context_manager.py`    | Ước lượng token, tóm tắt khi vượt ngưỡng |
| 3 | Tool registry           | `tool_registry.py`      | Đặc tả tool, phân loại quyền, dispatch |
| 4 | Sub-agent               | `subagent.py`           | Fork một child bị hạn chế cho tác vụ con |
| 5 | Primitive               | `tool_registry.py`      | `read_file`, `write_file`, `run_shell` |
| 6 | Bộ nhớ / persistence    | `persistence.py`        | Log JSONL append-only, replay |
| 7 | Lắp ráp system prompt   | `prompt_assembly.py`    | Đi ngược cây thư mục, append guideline, giữ prefix cache |
| 8 | Hook vòng đời           | `hooks.py`              | Callback trước/sau tool, cổng tin cậy |
| 9 | Cổng quyền shell        | `tool_registry.py`      | `classify_command` + leo thang tương tác |

Thành phần 3, 5, 9 cùng nằm trong `tool_registry.py` vì chúng dùng chung state: registry là nơi tự nhiên để giữ cả *cái gì có thể gọi* và *liệu lệnh gọi đó có được phép*.

## Ánh xạ tới năm subsystem được chấm điểm

`validate_harness.py` không chấm theo module; nó chấm theo *subsystem*. Mỗi thành phần đóng góp vào một hoặc hai subsystem:

| Subsystem      | Người đóng góp chính                                  | Cái mà bộ chấm điểm tìm |
|----------------|-------------------------------------------------------|--------------------------|
| Instructions   | `prompt_assembly.py`, `AGENTS.md`                     | Quy trình khởi động, Definition of Done, dẫn đường tới state |
| State          | `persistence.py`, `feature_list.json`, `progress.md`  | Log append-only, schema feature hợp lệ, dấu mốc restart |
| Verification   | `init.sh` / `init.ps1`, primitive của `tool_registry.py` | Fail-fast, lệnh test, ghi nhận evidence |
| Scope          | `feature_list.json`, `subagent.py`                    | Quy tắc một-feature-một-lần, đồ thị phụ thuộc, ranh giới fork |
| Lifecycle      | `harness.py`, `hooks.py`, `session-handoff.md`        | Vòng lặp có giới hạn, cổng tin cậy hook, câu chuyện restart |

## Khi nào mở rộng vs khi nào thay thế

**Mở rộng tại chỗ** nếu thay đổi giữ nguyên contract:
- Tool mới? Đăng ký trong `tool_registry.py`, thêm rule `classify_command` nếu có shell.
- Telemetry mới? Thêm post-tool hook trong `hooks.py`.
- Chiến lược tóm tắt mới? Kế thừa `ContextManager` và inject vào `Harness.__init__`.

**Thay thế** chỉ khi chính contract thay đổi:
- Lập kế hoạch nhiều bước vượt quá `run()` → viết một orchestrator mới và giữ `harness.py` làm leaf executor.
- Tác vụ chạy nền dài → thêm queue file trong `.harness/` và một worker module; đừng chặn vòng lặp chính.

## Hình dạng adapter cho LLM thật

`harness.py::Harness.run()` đi kèm một bộ sinh mock turn. Điểm tích hợp là một method duy nhất:

```python
def _model_turn(self, messages: list[dict]) -> dict:
    """Return {'role': 'assistant', 'content': str, 'tool_call': dict | None}."""
    ...
```

Cung cấp method đó (hoặc override qua subclass) thì mọi thứ khác — nén, cổng quyền, log — vẫn chạy không cần thay đổi. Giữ adapter trong code của caller, không phải trong module harness, để harness vẫn không có dependency.

## Liên quan

- [Architecture principles](architecture-principles.md) — invariant đứng sau những module này.
- [Tool registry and safety](tool-registry-and-safety.md) — thành phần 3, 5, 9.
- [Context and memory](context-and-memory.md) — thành phần 2, 6, 7.
- [Lifecycle and hooks](lifecycle-and-hooks.md) — thành phần 1, 8.
