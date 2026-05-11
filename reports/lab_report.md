# Báo cáo kết quả Lab Day 08

## 1. Thông tin sinh viên

- Họ và tên: Lương Hữu Thành
- Repository/Commit: https://github.com/fisherman611/2A202600114-LuongHuuThanh-phase2-track3-day8-langgraph-agent
- Ngày thực hiện: 11/05/2026

## 2. Kiến trúc hệ thống (Architecture)

Hệ thống được vận hành dựa trên khung sườn `StateGraph` của LangGraph, chịu trách nhiệm quản lý và điều phối luồng trạng thái toàn cục (global state dictionary). 
- **Các thành phần (Nodes)**: 
    - `prepare_input`: Thực hiện tiền xử lý và chuẩn hóa các truy vấn đầu vào từ người dùng.
    - `analyze_intent`: Phân tích ý định và điều hướng luồng công việc dựa trên kỹ thuật nhận diện từ khóa.
    - `execute_tool_logic`: Giả lập các thao tác nghiệp vụ tại hệ thống backend.
    - `verify_result`: Kiểm định đầu ra của công cụ để phân biệt giữa kết quả thành công và các lỗi tạm thời (transient faults).
    - `handle_authorization`: Thiết lập cổng phê duyệt có sự can thiệp của con người (Human-in-the-loop - HITL) đối với các hành động rủi ro cao.
    - `increment_retry`: Cơ chế quản lý số lần thử lại có giới hạn (bounded retry).
    - `finalize_response`: Tổng hợp và định dạng phản hồi cuối cùng gửi tới người dùng.
    - `wrap_up_session`: Kiểm soát và ghi nhật ký hoạt động trước khi kết thúc phiên làm việc.
- **Các kết nối (Edges)**: 
    - Các cạnh tĩnh (Static edges) kết nối các quy trình tuyến tính.
    - Các cạnh điều kiện (Conditional edges) cho phép rẽ nhánh linh hoạt dựa trên ý định người dùng, kết quả kiểm định và số lần thử lại thực tế.

## 3. Cấu trúc trạng thái (State Schema)

`GlobalState` được định nghĩa dưới dạng `TypedDict`, kết hợp giữa cơ chế ghi đè (overwrite) cho các trạng thái tức thời và cơ chế cộng dồn (append-only) thông qua `Annotated[list, add]` cho các trường phục vụ kiểm toán (audit).

| Trường dữ liệu | Cơ chế (Reducer) | Mục đích |
|---|---|---|
| node_history | append | Truy vết lộ trình di chuyển của Agent qua các node phục vụ đo lường. |
| execution_log | append | Lưu trữ nhật ký chi tiết về mọi hoạt động xử lý trong hệ thống. |
| error_stack | append | Tập hợp các thông báo lỗi tạm thời phục vụ phân tích và gỡ lỗi. |
| retry_count | overwrite | Cập nhật số lần thử lại hiện tại để kiểm soát vòng lặp. |
| selected_path | overwrite | Ghi nhận quyết định điều hướng cuối cùng từ bộ phân tích ý định. |

## 4. Kết quả kịch bản kiểm thử (Scenario Results)

Hệ thống đã hoàn thành xuất sắc tất cả 7 kịch bản kiểm thử với **tỷ lệ thành công đạt 100%**.

| Kịch bản | Luồng dự kiến | Luồng thực tế | Thành công | Số lần thử lại | Số lần ngắt (HITL) |
|---|---|---|---:|---:|---:|
| S01_simple | đơn giản | đơn giản | Có | 0 | 0 |
| S02_tool | công cụ | công cụ | Có | 0 | 0 |
| S03_missing | thiếu thông tin | thiếu thông tin | Có | 0 | 0 |
| S04_risky | rủi ro | rủi ro | Có | 0 | 1 |
| S05_error | lỗi | lỗi | Có | 2 | 0 |
| S06_delete | xóa dữ liệu | rủi ro | Có | 0 | 1 |
| S07_dead_letter | lỗi tới hạn | lỗi | Có | 1 | 0 |

## 5. Phân tích xử lý lỗi

1. **Xử lý lỗi hệ thống và công cụ**: Trong các kịch bản S05 và S07, hệ thống đã nhận diện chính xác các lỗi tạm thời thông qua node `verify_result`. Bằng cách điều hướng sang `increment_retry`, hệ thống đã thực hiện cơ chế thử lại một cách tự động và có kiểm soát, ngăn chặn tình trạng vòng lặp vô tận đồng thời tối đa hóa khả năng phục hồi dữ liệu.
2. **Kiểm soát hành động nhạy cảm**: Tại các kịch bản S04 và S06, bộ phân tích đã nhận diện các từ khóa mang tính rủi ro cao. Quy trình xử lý được chuyển hướng bắt buộc qua node `handle_authorization` sử dụng hàm `interrupt`. Điều này đảm bảo các thao tác quan trọng không bao giờ được thực thi nếu thiếu sự xác nhận trực tiếp từ quản trị viên.

## 6. Minh chứng về khả năng lưu trữ và phục hồi (Persistence)

Hệ thống tích hợp bộ lưu trữ **SQLite Checkpointer** (`SqliteSaver`). Mỗi kịch bản được định danh bằng một `thread_id` riêng biệt.
- **Minh chứng**: Chỉ số `interrupt_count` trong các kịch bản rủi ro cho thấy trạng thái của Agent đã được tạm dừng và khôi phục thành công từ bộ nhớ đệm.
- **Khả năng khôi phục sau sự cố**: Tệp dữ liệu `checkpoints.db` lưu trữ toàn bộ lịch sử trạng thái, cho phép Agent tiếp tục xử lý chính xác tại điểm bị gián đoạn ngay cả khi hệ thống bị khởi động lại đột ngột.

## 7. Các hạng mục mở rộng (Extension Work)

- **Lưu trữ SQLite**: Nâng cấp từ bộ nhớ tạm thời (`MemorySaver`) sang cơ sở dữ liệu SQLite bền vững để đảm bảo toàn vẹn dữ liệu giữa các phiên làm việc khác nhau.
- **Trực quan hóa đồ thị**: Phát triển công cụ xuất sơ đồ Mermaid tự động, giúp minh họa cấu trúc vận hành nội bộ của Agent một cách trực quan và khoa học.
- **Chuẩn hóa mã nguồn**: Đạt tỷ lệ tuân thủ 100% đối với các quy tắc kiểm tra nghiêm ngặt của `ruff` và `mypy`, đảm bảo chất lượng và tính bảo trì của mã nguồn.

## 8. Kế hoạch cải tiến

Nếu có thêm thời gian phát triển, tôi sẽ ưu tiên các hạng mục sau:
1. **Bộ điều hướng dựa trên LLM**: Thay thế logic từ khóa bằng mô hình ngôn ngữ lớn để xử lý các truy vấn phức tạp và đa dạng về ngữ nghĩa.
2. **Tích hợp RAG**: Cho phép Agent truy xuất thông tin thực tế từ cơ sở tri thức thay vì sử dụng logic giả lập, nhằm cung cấp câu trả lời chính xác hơn.
3. **Giám sát chuyên sâu (Tracing)**: Tích hợp LangSmith để theo dõi độ trễ và chi phí tài nguyên ở mức độ chi tiết nhất.
