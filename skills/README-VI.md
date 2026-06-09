# Hướng Dẫn Sử Dụng & Chạy Bộ Harness Kit (Python)

Tài liệu này hướng dẫn cách cài đặt, chạy thử nghiệm và tích hợp bộ công cụ Harness Python tối giản (Standard-library-only) dành cho các AI Agent.

---

## 1. Yêu Cầu Hệ Thống
* **Python**: Phiên bản 3.8 trở lên.
* **Hệ điều hành**: Windows (PowerShell/CMD) hoặc macOS/Linux.
* **Dependencies**: **Không cần cài đặt bất kỳ thư viện ngoài nào (Không cần `pip install`)**. Bộ kit sử dụng 100% thư viện chuẩn đi kèm Python để đảm bảo tính gọn nhẹ và an toàn cao nhất trong mọi môi trường sandbox.

---

## 2. Cấu Trúc Các Thành Phần
Các tệp mẫu nằm trong thư mục `templates/`:
* [harness.py](templates/harness.py): Tệp chạy chính điều phối vòng lặp `while` và kết nối toàn bộ hệ thống con.
* [context_manager.py](templates/context_manager.py): Tính toán token ước lượng và kích hoạt cơ chế nén ngữ cảnh (compaction).
* [tool_registry.py](templates/tool_registry.py): Đăng ký các công cụ (đọc/ghi file, chạy shell) và phân quyền an toàn.
* [persistence.py](templates/persistence.py): Lưu trữ trạng thái phiên làm việc dưới dạng append-only JSON Line.
* [hooks.py](templates/hooks.py): Đăng ký các hàm trung gian chạy trước và sau khi gọi công cụ (pre/post hooks).
* [subagent.py](templates/subagent.py): Khởi chạy và giới hạn quyền hạn của các Sub-agent (tác nhân con).
* [prompt_assembly.py](templates/prompt_assembly.py): Tự động tìm kiếm chỉ dẫn dự án để lắp ráp vào Prompt hệ thống động.

---

## 3. Hướng Dẫn Chạy Thử Nghiệm

Bộ kit hỗ trợ chế độ **Giả lập (Mock Mode)** để bạn có thể quan sát trực quan cách 9 thành phần của Harness tương tác với nhau mà không cần cấu hình API Key hay tốn phí Token.

### Bước 1: Di chuyển vào thư mục gốc của dự án
Mở terminal và di chuyển đến thư mục chứa dự án `harness-kit`.

### Bước 2: Biên dịch kiểm tra cú pháp (Syntax Check)
Trước khi chạy, hãy đảm bảo tất cả các file Python không có lỗi cú pháp:

* **Trên Windows (PowerShell)**:
  ```powershell
  Get-ChildItem -Path "skills/templates/*.py" | ForEach-Object { py -m py_compile $_.FullName }
  ```
* **Trên macOS/Linux**:
  ```bash
  python3 -m py_compile skills/templates/*.py
  ```

### Bước 3: Chạy chế độ giả lập (Mock Mode)
Chạy lệnh sau để giả lập vòng lặp xử lý tác vụ của Agent:

* **Trên Windows**:
  ```powershell
  py -m skills.templates.harness --mock --goal "Tạo một lớp Calculator đơn giản"
  ```
* **Trên macOS/Linux**:
  ```bash
  python3 -m skills.templates.harness --mock --goal "Tạo một lớp Calculator đơn giản"
  ```

### Quan sát quá trình thực thi trong Mock Mode:
1. **Khởi tạo và Replay**: Hệ thống kiểm tra xem có tệp nhật ký phiên làm việc cũ không. Nếu có, nó sẽ tự động phát lại (replay) để phục hồi ngữ cảnh.
2. **Lượt 1 (Iteration 1)**: LLM quyết định gọi công cụ `spawn_subagent` để kiểm tra cấu trúc thư mục. Lớp Hook sẽ bắt được cuộc gọi (Pre-Hook), chạy sub-agent trong môi trường cô lập, và trả về kết quả cho luồng chính.
3. **Lượt 2 (Iteration 2)**: LLM quyết định gọi công cụ ghi file (`write_file`) để viết mã nguồn cho file `calculator.py`.
4. **Lượt 3 (Iteration 3)**: LLM gọi lệnh shell (`run_shell`) để kiểm tra compile mã nguồn vừa tạo. Bộ đăng ký công cụ (`tool_registry`) sẽ phân loại lệnh động, phát hiện đây là lệnh an sau và cho phép chạy.
5. **Lượt 4 (Iteration 4)**: Hệ thống ghi nhận mục tiêu đã hoàn thành và thoát vòng lặp an toàn.

---

## 4. Nhật Ký Phiên Làm Việc (Durability Logs)
* Sau khi chạy, Harness sẽ tự động tạo thư mục `.harness/` chứa file `main_session.jsonl` tại thư mục làm việc của bạn.
* Bạn có thể mở file này ra xem: mỗi dòng là một sự kiện (event) được ghi nhận độc lập dưới dạng JSON. Nếu tiến trình bị tắt đột ngột, việc chạy lại lệnh trên sẽ tự động đọc lại tệp `.jsonl` này để phục hồi trạng thái mà không làm mất lịch sử hội thoại trước đó.

Để dọn dẹp các tệp tạm tạo ra sau quá trình chạy thử nghiệm, bạn có thể xóa file `calculator.py` và thư mục `.harness/`:
```bash
# Windows
Remove-Item -Path "calculator.py" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".harness" -Recurse -Force -ErrorAction SilentlyContinue

# macOS / Linux
rm -f calculator.py
rm -rf .harness
```

---

## 5. Hướng Dẫn Tích Hợp Live Mode (Sử dụng API thực tế)
Để đưa bộ kit này vào hoạt động thực tế với các API của OpenAI hoặc Anthropic:
1. Nhập các module này vào ứng dụng chính của bạn:
   ```python
   from skills.templates.harness import Harness
   ```
2. Thay thế hàm `_simulate_mock_turn` trong `harness.py` bằng lời gọi API thực tế tới LLM của bạn (như gửi danh sách `history` và danh sách công cụ từ `self.registry.get_descriptors()`).
3. Đảm bảo cấu hình biến môi trường bảo mật phù hợp và cấp quyền an toàn trước khi chạy Agent trên kho mã nguồn thực tế.
