---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia (MediaWiki Action API)
requires_env: []
inputs: [query, lang, max_results]
outputs: [title, url, source, summary]
side_effect: false
---
# wiki

Tìm bài Wikipedia khớp nhất với `query` và trả về đoạn tóm tắt mở đầu (tối đa 5 câu).

- Một request duy nhất: `generator=search` + `prop=extracts|info` trên `https://{lang}.wikipedia.org/w/api.php`.
- Không cần API key. Gửi `User-Agent` chung theo yêu cầu của Wikimedia.
- `lang`: `vi` hoặc `en`; giá trị khác → fallback `en`.
- `max_results`: ép kiểu int và kẹp trong 1..5; giá trị không hợp lệ → 1.
- `query` rỗng → trả error dict, không gọi network.
- Lỗi HTTP/timeout → trả error dict (`{"tool": "wiki", "error": ..., "message": ...}`), không raise.

Dùng cho câu hỏi định nghĩa / khái niệm / tiểu sử ổn định ("X là gì", "X là ai").
Không dùng cho tin tức mới (→ `lookup`) hay bài đăng mạng xã hội (→ `social_search` / `timeline`).
