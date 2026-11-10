# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: hahavuiqua
- Members: Vũ Đức Minh; Đặng Việt Anh; Lê Xuân Phúc
- Provider/model: OpenRouter; Gemini; OpenAI

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Tôi là trợ lý nghiên cứu hỗ trợ bạn tìm kiếm tin tức, mạng xã hội, trích xuất dữ liệu từ các liên kết và bài báo khoa học một cách chính xác. Bên cạnh đó, tôi có thể giải đáp thắc mắc, phân tích và trình bày thông tin bài viết theo đúng yêu cầu của bạn.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
| :--- | :--- | :--- |
| `lookup` | Tra cứu thông tin và tin tức mới nhất trên Internet | Không |
| `fetch` | Đọc và lấy nội dung chi tiết từ một đường dẫn URL | Không |
| `social_search` | Tìm kiếm các bài viết, thảo luận trên mạng xã hội | Không |
| `timeline` | Xem bài đăng gần nhất từ một tài khoản mạng xã hội cụ thể | Không |
| `papers` | Tìm kiếm bài báo khoa học (arXiv) theo từ khóa | Không |
| `paper_text` | Trích xuất nội dung văn bản chi tiết của bài báo khoa học | Không |
| `policy` | Tìm kiếm tài liệu, chính sách và quy định nội bộ | Không |
| `format` | Định dạng và tổng hợp dữ liệu thu thập thành bài viết hoàn chỉnh | Không |
| `send` | Gửi tin nhắn/nội dung đi (yêu cầu người dùng xác nhận trước) | Không |
| `clarify` | Gửi câu hỏi làm rõ thông tin hoặc xin xác nhận từ người dùng | Không |
| `wiki` | Tra Wikipedia để lấy đoạn tóm tắt mở đầu của bài viết khớp nhất | Có |

## A3. Câu hỏi mẫu để thử

1. MCK là ai?
2. Gửi những nội dung vừa tìm hiểu đi
3. Elon Musk đang nói vấn đề gì hay ho?

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo lường hành vi routing và argument của prompt và tools hiện tại trên Gemini | — | 1.00 | `runs/v0_B_base_gemini_20261110T124141631477.json` |
| v1 | system_prompt.md | Kiểm tra tính nhất quán và độ ổn định của system prompt và tools | 1.00 | 1.00 | `runs/v1_B_base_gemini_20261110T125450617023.json` |
| v2 | system_prompt.md | Xác định các case biên bị ảnh hưởng bởi cách diễn giải câu chữ của Gemini (R01, R03) | 1.00 | 0.90 | `runs/v2_B_base_gemini_20261110T140452370260.json` |
| v2 | tools.yaml | Giữ nguyên từ khóa gốc, không dịch hoặc mở rộng (sửa R03) | 0.90 | 0.95 | `runs/v2_B_base_gemini_20261110T142047801634.json` |
| v2 | tools.yaml | Thử điều chỉnh schema `screenname` để xử lý R01 | 0.95 | 0.95 | `runs/v2_B_base_gemini_20261110T142519201562.json` |
| v2 | tools.yaml | Nêu rõ ánh xạ Sam Altman sang `sama` để sửa R01 | 0.95 | 1.00 | `runs/v2_B_base_gemini_20261110T142832168454.json` |
| v3 | tools.yaml | Xác nhận độ hội tụ trên 20 base test case sau khi xử lý lỗi routing và arguments | 1.00 | 1.00 | `runs/v3_B_base_gemini_20261110T143016470366.json` |

## B2. Failure Analysis

Tổng hợp lỗi thực tế trong các run; run nhóm cuối đạt 15/15.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R01_user_tweets_routing | `wrong_tool` | Gọi `clarify` thay vì `timeline` | Không tự ánh xạ Sam Altman sang handle `sama`; lỗi còn ở các run `v2` trước khi hoàn tất sửa. | Thêm quy tắc ánh xạ Sam Altman → `sama` trong `tools.yaml`; run `v2_B_base_gemini_20261110T142832168454.json` đạt 20/20. |
| R03_web_news_routing | `wrong_arg_value` | `lookup(query="Trí tuệ nhân tạo AI", topic="news", timeframe="day")` | Từ khóa gốc `AI` bị tự dịch/mở rộng. | Yêu cầu giữ nguyên từ khóa gốc trong mô tả `lookup`; run `v2_B_base_gemini_20261110T142047801634.json` cải thiện lên 19/20. |
| G02_news_lookup_timeframe | `wrong_arg_value` | `lookup(topic="general", timeframe="year")` | Sai phân loại tin tức và khoảng thời gian; mong đợi `news` và `week`. | Run nhóm cuối `v3_B_group_gemini_20261110T145629117171.json` đạt |
| G03_social_top_search | `wrong_arg_value` | Gọi `social_search` và gọi thừa `lookup` | Dùng thêm tìm kiếm web không cần thiết khi yêu cầu tìm bài nổi bật trên mạng xã hội. | Run nhóm cuối đạt |
| G08_arxiv_papers_search | `wrong_arg_value` | `papers(query="Large Language Model reasoning", max_results=5)` | User yêu cầu 3 bài nhưng tool nhận `max_results=5`. | Run nhóm cuối đạt |
| G10_multiturn_switch_from_web_to_twitter | `wrong_arg_value` | `timeline(screenname="gregbrockman")` | Chuyển đúng sang `timeline` nhưng handle không khớp kỳ vọng `gdb`. | Run nhóm cuối đạt |

## B3. Team Eval Cases

`eval_group.json` hiện có 17 case (10 single-turn, 7 multi-turn), khác với ghi chú mẫu 10 case. Run nhóm cuối bên dưới chỉ chứa G01–G15.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_timeline_stripping_at_symbol | Bỏ `@` khỏi handle và giữ limit | `timeline(screenname="KimKardashian", limit=5)` | PASS |
| G02_news_lookup_timeframe | Định tuyến tin tức và thời gian tuần | `lookup(topic="news", timeframe="week")` | PASS |
| G03_social_top_search | Tìm bài nổi bật trên mạng xã hội | `social_search(search_type="Top")` | PASS |
| G04_missing_target_summary | Hỏi làm rõ khi thiếu URL/bài viết | `clarify` | PASS |
| G05_unconfirmed_telegram_post | Xin xác nhận trước hành động gửi | `clarify(response_type="yes_no")` | PASS |
| G06_out_of_scope_creative_writing | Không gọi tool cho yêu cầu ngoài phạm vi | Không gọi tool; từ chối/yêu cầu phù hợp | PASS |
| G07_unnecessary_tool_common_calc | Trả lời kiến thức thường thức trực tiếp | Không gọi tool | PASS |
| G08_arxiv_papers_search | Định tuyến tìm paper arXiv và giữ số lượng | `papers(max_results=3)` | PASS |
| G09_multiturn_clarify_then_social_search | Dùng chủ đề được bổ sung sau clarify | `social_search(query="Nvidia Blackwell")` | PASS |
| G10_multiturn_switch_from_web_to_twitter | Đổi từ web sang timeline và ánh xạ Greg Brockman | `timeline(screenname="gdb")` | PASS |
| G11_multiturn_correct_timeframe | Cập nhật timeframe trong hội thoại | `lookup(query="AI", topic="news", timeframe="month")` | PASS |
| G12_multiturn_confirm_and_send | Chỉ gửi sau khi người dùng xác nhận | `send(confirmed=true)` | PASS |
| G13_multiturn_url_followup_fetch | Dùng URL được bổ sung ở lượt sau | `fetch(url="https://techcrunch.com/2026/ai-breakthrough")` | PASS |
| G14_multiturn_change_account_and_limit | Thay tài khoản và limit trong lượt sau | `timeline(screenname="demishassabis", limit=10)` | PASS |
| G15_multiturn_out_of_scope_pivot | Không gọi tool cho câu hỏi kiến thức lập trình | Không gọi tool; trả lời trực tiếp | PASS |
| G16_wiki_concept_definition | Định tuyến câu hỏi khái niệm ổn định vào tool mới | `wiki(lang="vi")` | Chưa có trong run nhóm |
| G17_wiki_vs_news_boundary | Phân biệt tin mới với tra cứu bách khoa | `lookup(topic="news", timeframe="day")` | Chưa có trong run nhóm |

## B4. Live Chat Evidence

Các transcript dưới đây ghi lại hội thoại trực tiếp; trạng thái PASS/FAIL của chúng không phải kết quả eval tự động.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| `v3_gemini_20261110T091907448608`, turn 2 | “MCK là ai” | `wiki(query="MCK", lang="vi")` | v3; transcript ghi tool result từ Wikipedia tiếng Việt | Trả lời có tóm tắt và thông tin nguồn từ Wikipedia. |
| `v3_gemini_20261110T161118027429`, turn 3 | “Search me twitter of kim kardashian” | `timeline(screenname="KimKardashian")` | v3; `gemini-3.5-flash` | Trả về 5 bài đăng gần đây; handle không có ký tự `@`. |
| `v3_gemini_20261110T161245742479`, turns 2–4 | Yêu cầu gửi bản tin Telegram, xác nhận, rồi cung cấp chủ đề Kim Kardashian | `clarify(yes_no)` → `clarify(text)` → `lookup` → `format`; không có sự kiện gọi `send` được ghi lại | v3; transcript dừng sau khi tạo nội dung bản tin | Đã hỏi xác nhận và làm rõ nội dung, nhưng chưa có bằng chứng tin nhắn được gửi; lượt cuối chứa JSON gọi `send` dưới dạng văn bản assistant. |
| `v3_gemini_20261110T162028466638`, turn 2 | “Cho tôi tiền đi” | Không có | v3; transcript có hai lượt, không ghi model | Trả lời trực tiếp trong phạm vi trợ lý nghiên cứu, không gọi tool. |

## B6. Reflection

- **Fix thuộc `system_prompt.md`:** Version log không ghi nhận thay đổi prompt có cải thiện điểm số; v1 giữ nguyên 1.00, còn v2 giảm xuống 0.90 khi phát hiện độ biến động ở R01 và R03. Vì vậy, chưa có bằng chứng trong log để kết luận cần sửa prompt cho hai lỗi này.
- **Fix thuộc `tools.yaml`:** R03 được cải thiện từ 0.90 lên 0.95 khi mô tả `lookup` yêu cầu giữ nguyên từ khóa gốc, không dịch hoặc mở rộng. Với R01, điều chỉnh schema `screenname` chưa làm điểm tăng (0.95 → 0.95), nhưng quy tắc ánh xạ rõ Sam Altman → `sama` giúp tăng lên 1.00. v3 giữ 1.00 trên 20 base test case.
- **Cần review thủ công:** R03 cần kiểm tra xem từ khóa có bị dịch hoặc diễn giải thêm ngoài yêu cầu hay không; R01 cần xác nhận handle được ánh xạ đúng theo ý người dùng. Chỉ nhìn điểm tổng không cho biết chính xác phản hồi nào sai hoặc mức độ phù hợp về ngữ nghĩa.
- **Cải thiện tiếp:** Bổ sung regression case riêng cho R01 và R03; kiểm tra output/tool arguments của từng run, không chỉ điểm tổng; tiếp tục thay đổi từng phần và ghi rõ giả thuyết cùng run tương ứng trong version log.
