# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team:
- Members:
- Provider/model:

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì (cho team khác hiểu nhanh).

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận."

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: 

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin hoặc xin xác nhận trước khi gửi | không |
| timeline | lấy tweet gần đây của một tài khoản X cụ thể | không |
| social_search | tìm tweet theo chủ đề/từ khóa (Latest/Top) | không |
| lookup | tìm tin tức / thông tin trên web (Tavily), lọc theo thời gian | không |
| fetch | đọc nội dung một URL (Firecrawl) | không |
| format | trình bày kết quả thành markdown digest | không |
| send | gửi bản tin lên Telegram (chỉ sau khi user xác nhận) | không |
| policy | tra company policy nội bộ | không |
| papers | tìm paper trên arXiv | không |
| paper_text | đọc nội dung PDF paper arXiv | không |
| **wiki** | tra Wikipedia (vi/en): tóm tắt khái niệm, người, tổ chức — "X là gì / là ai" | **có** |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1.
2.
3.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |
| v1 |  |  |  |  |  |
| v2 |  |  |  |  |  |
| v3 |  |  |  |  |  |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

Run v0: `runs/v0_B_base_openrouter_20261110T094950522888.json` — 13/20 pass (case_accuracy 0.65, tool_routing 0.75, argument 0.65, multiturn 1.0).

Failure Type = nhãn `failure_type` của case trong `eval_base.json`; trong ngoặc là `observed_mismatch` thực tế từ run JSON.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_tool (observed: wrong_arg_value) | `lookup(query="AI news", topic="news", timeframe="day")` | Chọn đúng tool nhưng model tự thêm "news" vào `query`; expected `query="AI"` | `tools.yaml`: giữ nguyên từ khóa của user trong `query`, dùng `topic=news` để lọc tin tức |
| R13_parallel_web_and_tweets | wrong_tool (observed: wrong_arg_value) | `lookup(query="AI news", timeframe="day")` + `social_search(query="AI", search_type="Latest")` | `lookup` sai `query` ("AI news" thay vì "AI") và thiếu `topic="news"` | `tools.yaml` + prompt: rule "tin tức → `topic=news`", không nhồi từ "news" vào query |
| R08_out_of_scope | out_of_scope (observed: unexpected_tool_call) | `send(text="Nguyên hàm của x^2 là …")` | Câu hỏi toán ngoài phạm vi research, expected no tool, model lại gọi `send` | Prompt: request ngoài scope → trả lời ngắn/từ chối, không gọi tool; bỏ chỉ dẫn xấu khuyến khích gửi |
| R14_out_of_scope_coding | out_of_scope (observed: unexpected_tool_call) | `send(text="Dưới đây là một hàm Python tính số Fibonacci…")` | Yêu cầu viết code ngoài scope, model gọi `send` | Như R08 |
| R10_missing_handle | missing_info (observed: missing_tool_call) | `timeline(screenname="sama")` | Không có handle, model tự đoán thay vì `clarify` | Prompt: bỏ chỉ dẫn "đoán thay vì hỏi"; thiếu account → `clarify` |
| R11_missing_url | missing_info (observed: missing_tool_call) | `fetch(url="https://example.com/article")` | Bịa URL thay vì hỏi lại | Prompt: thiếu URL → `clarify`, không bịa URL |
| R12_confirm_before_send | wrong_boundary (observed: missing_tool_call) | `send(text="Bản tin này")` | Gửi Telegram khi user chưa xác nhận; expected `clarify` | Prompt + `tools.yaml`: `send` chỉ gọi khi user đã xác nhận (`confirmed=true`), chưa xác nhận → `clarify` |

Nhận xét: 5/7 lỗi (R08, R10, R11, R12, R14) đến từ các chỉ dẫn xấu cố ý trong `system_prompt.md` (đoán thay vì hỏi, gửi không cần xác nhận) → giả thuyết v1. 2/7 lỗi (R03, R13) là convention args của `lookup` → giả thuyết cho `tools.yaml` ở vòng sau.

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

Transcript: `transcripts/v4_openrouter_20261110T113858580135.transcript.json` — `artifact_version = v4+pcb4acb4b03a4+t46215275f381`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 (KB1: research — tool mới) | "Chat GPT là gì ?" | `wiki(query="ChatGPT", lang="vi")` | v4+pcb4acb4b03a4+t46215275f381 | ✅ Route đúng tool mới `wiki`, chuẩn hoá query "Chat GPT" → "ChatGPT"; trả lời tóm tắt từ vi.wikipedia |
| 2 (KB1: research bình thường) | "Tin AI hôm nay có gì nổi bật?" | `lookup(query="AI", topic="news", timeframe="day")` | v4+pcb4acb4b03a4+t46215275f381 | ✅ Đúng tool + đúng convention args (query cốt lõi, `topic=news`, `timeframe=day`); trả lời danh sách tin có nguồn |
| 3 (KB2: thiếu thông tin) | "Tóm tắt 5 tweet mới nhất giúp mình" | *(không gọi tool)* — trả lời text: "Bạn muốn xem tweet của tài khoản nào?" | v4+pcb4acb4b03a4+t46215275f381 | ⚠️ Hành vi đúng với user (hỏi lại, không đoán tài khoản), nhưng hỏi bằng text thay vì gọi `clarify` → transcript ghi `status=answered` thay vì `waiting_for_user`. Eval R10 vẫn PASS vì `run_eval.py` ép `tool_choice="required"`, còn `chat.py` không ép |
| 4 (KB2: bổ sung) | "Của Sam Altman" | `timeline(screenname="sama", limit=5)` | v4+pcb4acb4b03a4+t46215275f381 | ✅ Ghép đúng ngữ cảnh lượt 3: đổi tên → handle `sama` (không `@`), giữ `limit=5`; trả 5 tweet kèm link x.com |

Nhận xét: eval đo hành vi khi bắt buộc gọi tool, còn chat live cho model tự chọn. Lượt 3 cho thấy khoảng cách giữa hai môi trường này — hướng sửa tiếp theo (nếu cần): thêm vào `system_prompt.md` "khi cần hỏi lại user, LUÔN dùng tool `clarify`, không hỏi bằng text thường".

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
| Tool mới `wiki` | `tools/wiki/tool.py`, `tools/wiki/TOOL.md`, `runs/v4_B_group_openrouter_20261110T110237954127.json` | G11 → `wiki(query="Transformer", lang="vi")`; G12 → `wiki(query="Retrieval-augmented generation", lang="en")`; G13 (tin tức về người) → vẫn `lookup(news, week)`, không nhầm sang wiki. v4 giữ base 20/20, extension 10/10 | Không cần API key; query rỗng → error dict, không gọi network; lang/max_results từ model được chuẩn hoá |
| Tool unit tests (`tests/`) | `pytest` output: 73 passed, 14 skipped (skip = stub TODO của tool có sẵn) | 6 test cho `wiki` trong `tests/test_tools_todo.py` |  |

Tool unit tests — `wiki` (6 test, offline bằng `fake_http`):

1. `test_wiki_sends_search_request_and_maps_best_match` — happy path: assert URL, params (`gsrsearch`, `gsrlimit`, `generator`), có `User-Agent`, và mapping kết quả sắp xếp theo thứ hạng tìm kiếm (`index`), không theo thứ tự API trả.
2. `test_wiki_empty_query_returns_error_without_network` — query `""`, `"   "`, `None` → `ValueError` dict, không có request nào.
3. `test_wiki_normalizes_bad_lang_and_max_results_from_model` — input xấu từ model: `lang="fr"`/`"EN"`/`None`, `max_results="3"`/`0`/`"abc"`/`99` → lang fallback `en`, max_results kẹp 1..5.
4. `test_wiki_no_match_returns_empty_items` — API không có key `query` → `items=[]`, không lỗi.
5. `test_wiki_http_error_returns_error_dict` — HTTP 429 → error dict, không raise.
6. `test_wiki_timeout_returns_error_dict` — timeout → error dict.

Ví dụ lỗi unit test bắt được mà eval không bắt được: eval chỉ kiểm tra model gọi `wiki(lang="vi")`; nếu code quên dùng `lang` để chọn domain (luôn gọi `en.wikipedia.org`) thì eval vẫn PASS nhưng user nhận bài tiếng Anh — test số 3 bắt lỗi này qua assert `calls[i]["url"]`.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
