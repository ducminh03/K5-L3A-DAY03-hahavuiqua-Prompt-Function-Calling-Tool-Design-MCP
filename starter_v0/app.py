from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    assistant_tool_message,
    execute_tool_call,
    safe_slug,
    tool_results_message,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)

st.set_page_config(
    page_title="AI Research Agent — Day 03 Lab",
    page_icon="🔍",
    layout="wide",
)

# ----------------- Load Configurations -----------------
system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
tools_path = ARTIFACTS_DIR / "tools.yaml"

system_prompt = system_prompt_path.read_text(encoding="utf-8")
tool_declarations = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(tool_declarations)

# ----------------- Sidebar -----------------
with st.sidebar:
    st.title("🤖 Cấu hình Agent")

    provider_name = st.selectbox(
        "Model Provider",
        options=["gemini", "openrouter", "openai", "ollama"],
        index=0,
        help="Chọn nhà cung cấp mô hình LLM",
    )

    version_label = st.text_input("Phiên bản (Version)", value="v3")

    artifact_version = build_artifact_version(version_label, system_prompt_path, tools_path)
    st.caption(f"**Artifact Version:** `{artifact_version.artifact_version}`")

    st.divider()
    st.subheader("🛠️ Danh sách Tools")
    tool_names = [t["name"] for t in tool_declarations]
    st.write(", ".join([f"`{name}`" for name in tool_names]))

    st.divider()
    if st.button("🗑️ Xóa lịch sử / Phiên mới", use_container_width=True):
        st.session_state.messages = []
        st.session_state.transcript = None
        st.rerun()

# ----------------- Session State -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "transcript" not in st.session_state or st.session_state.transcript is None:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version_label), safe_slug(provider_name), timestamp])
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"

    st.session_state.transcript_path = transcript_path
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        "version": version_label,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": 5,
        "max_tool_rounds": 4,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "turns": [],
    }

# ----------------- Main Chat Header -----------------
st.title("🔍 Research Agent — Interactive Demo")
st.markdown(
    "Trợ lý nghiên cứu tự động: tra cứu web tin tức (`lookup`), trích xuất nội dung URL (`fetch`), "
    "đọc bài đăng mạng xã hội (`timeline`, `social_search`), tìm bài báo khoa học (`papers`), "
    "và kiểm tra chính sách công ty (`policy`)."
)

# Suggested queries if empty
if not st.session_state.messages:
    st.info("💡 **Gợi ý câu hỏi thử nghiệm:**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📰 Tin tức AI hôm nay có gì nổi bật?", use_container_width=True):
            st.session_state.suggested_input = "Tin tức AI hôm nay có gì nổi bật?"
        if st.button("🐦 Tweet mới nhất của Sam Altman là gì?", use_container_width=True):
            st.session_state.suggested_input = "Tweet mới nhất của Sam Altman là gì?"
    with col2:
        if st.button("📄 Tóm tắt link: https://openai.com/research/", use_container_width=True):
            st.session_state.suggested_input = "Tóm tắt link này giúp mình: https://openai.com/research/"
        if st.button("📚 Tìm 3 bài báo mới trên arXiv về LLM reasoning", use_container_width=True):
            st.session_state.suggested_input = "Tìm 3 bài nghiên cứu khoa học mới nhất trên arXiv về Large Language Model reasoning"

# Render conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("tool_events"):
            with st.expander("🛠️ Chi tiết công cụ đã gọi trong lượt này", expanded=False):
                for event in msg["tool_events"]:
                    st.markdown(f"**Tool:** `{event.get('tool')}`")
                    st.json(event.get("args", {}))
                    res = event.get("result", {})
                    if "items" in res:
                        st.markdown(f"*Trả về {len(res['items'])} items.*")
                    elif "error" in res:
                        st.error(f"Lỗi: {res.get('error')} - {res.get('message')}")
        st.markdown(msg["content"])

# ----------------- User Input & Execution Loop -----------------
user_input = st.chat_input("Nhập câu hỏi hoặc yêu cầu nghiên cứu...")

if "suggested_input" in st.session_state and st.session_state.suggested_input:
    user_input = st.session_state.suggested_input
    st.session_state.suggested_input = None

if user_input:
    # 1. Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Process with Provider & Agent Loop
    with st.chat_message("assistant"):
        provider = make_provider(provider_name)
        selected_model = getattr(provider, "default_model", None)

        working_messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages[-10:]:
            working_messages.append({"role": m["role"], "content": m["content"]})

        assistant_final_text = ""
        turn_tool_events: list[dict[str, Any]] = []
        turn_rounds: list[dict[str, Any]] = []

        with st.status("🧠 Agent đang suy nghĩ và chọn công cụ...", expanded=True) as status_box:
            for round_idx in range(1, 5):
                response = provider.complete(working_messages, openai_tools, model=selected_model, temperature=0.0)
                calls = response.tool_calls

                round_record = {
                    "round": round_idx,
                    "assistant_text": response.text,
                    "tool_calls": [{"name": c.name, "args": c.args} for c in calls],
                    "tool_results": [],
                }

                if not calls:
                    round_record["tool_results"] = []
                    turn_rounds.append(round_record)
                    assistant_final_text = response.text or "Đã hoàn thành yêu cầu."
                    status_box.update(label="✅ Đã xử lý xong!", state="complete", expanded=False)
                    break

                working_messages.append(assistant_tool_message(response.text, calls))
                non_clarify_events: list[dict[str, Any]] = []

                for call in calls:
                    status_box.write(f"🔧 **Đang gọi tool:** `{call.name}` với tham số: `{call.args}`")
                    event = execute_tool_call(call)
                    round_record["tool_results"].append(event)
                    turn_tool_events.append(event)

                    res = event.get("result", {})
                    if isinstance(res, dict) and res.get("awaiting_user"):
                        q = res.get("question") or call.args.get("question") or "Bạn bổ sung thêm thông tin nhé."
                        assistant_final_text = q
                        status_box.update(label="❓ Cần người dùng làm rõ thêm thông tin", state="complete", expanded=False)
                        break

                    non_clarify_events.append(event)

                turn_rounds.append(round_record)
                if assistant_final_text:
                    break

                working_messages.append(tool_results_message(non_clarify_events))

            if not assistant_final_text:
                assistant_final_text = "Đã đạt giới hạn số vòng gọi tool."
                status_box.update(label="⚠️ Đạt giới hạn lượt gọi công cụ", state="complete", expanded=False)

        # Show tool expander if tools were called
        if turn_tool_events:
            with st.expander("🛠️ Chi tiết công cụ đã gọi trong lượt này", expanded=False):
                for event in turn_tool_events:
                    st.markdown(f"**Tool:** `{event.get('tool')}`")
                    st.json(event.get("args", {}))
                    res = event.get("result", {})
                    if "items" in res:
                        st.markdown(f"*Trả về {len(res['items'])} items.*")
                    elif "error" in res:
                        st.error(f"Lỗi: {res.get('error')} - {res.get('message')}")

        st.markdown(assistant_final_text)

        # 3. Save assistant message and update transcript
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_final_text,
            "tool_events": turn_tool_events,
        })

        turn_log = {
            "turn_index": len(st.session_state.transcript["turns"]) + 1,
            "user_input": user_input,
            "assistant_response": assistant_final_text,
            "rounds": turn_rounds,
        }
        st.session_state.transcript["turns"].append(turn_log)
        write_transcript(st.session_state.transcript_path, st.session_state.transcript)
