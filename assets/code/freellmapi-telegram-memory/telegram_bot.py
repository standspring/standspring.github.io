"""Personal Telegram -> FreeLLMAPI bot with bounded, in-memory conversation history."""

import asyncio
import logging
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters


MAX_TURNS = 10
MAX_HISTORY_CHARS = 12000
MAX_INPUT_CHARS = 4000
SYSTEM_PROMPT = "한국어로 이해하기 쉽게 답하세요. 제공된 이전 대화가 있으면 이어서 답하세요."


def settings():
    load_dotenv(Path(__file__).with_name(".env"), override=False)
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    key = os.getenv("FREELLMAPI_API_KEY", "").strip()
    owner = os.getenv("ALLOWED_TELEGRAM_USER_ID", "").strip()
    if not token or token.startswith("PASTE_"):
        raise ValueError(".env에 TELEGRAM_BOT_TOKEN을 입력하세요.")
    if owner and (not owner.isascii() or not owner.isdecimal() or int(owner) <= 0):
        raise ValueError("ALLOWED_TELEGRAM_USER_ID에는 /id로 확인한 양의 정수를 입력하세요.")
    if owner and (not key or key.startswith("PASTE_")):
        raise ValueError(".env에 FreeLLMAPI 통합 키를 입력하세요.")
    return {
        "token": token,
        "owner": int(owner) if owner else None,
        "key": key,
        "base": os.getenv("FREELLMAPI_BASE_URL", "http://127.0.0.1:3001/v1").strip().rstrip("/"),
        "model": os.getenv("FREELLMAPI_MODEL", "auto").strip() or "auto",
    }


def authorized(update, config):
    return bool(
        config["owner"]
        and update.effective_chat
        and update.effective_chat.type == "private"
        and update.effective_user
        and update.effective_user.id == config["owner"]
    )


def history_chars(history):
    return sum(len(question) + len(answer) for question, answer in history)


def trim_history(history):
    # Copy first; a failed request must not change the saved history.
    kept = list(history)
    while kept and (len(kept) > MAX_TURNS or history_chars(kept) > MAX_HISTORY_CHARS):
        kept.pop(0)  # Remove a complete question/answer pair, oldest first.
    return kept


def build_messages(history, text):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for question, answer in trim_history(history):
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": answer})
    messages.append({"role": "user", "content": text})
    return messages


async def identify(update, context):
    if update.effective_chat and update.effective_chat.type == "private":
        await update.effective_message.reply_text(
            f"내 사용자 ID: {update.effective_user.id}\n"
            "이 숫자를 .env의 ALLOWED_TELEGRAM_USER_ID에 넣고 봇을 재시작하세요."
        )


async def welcome(update, context):
    config = context.bot_data["config"]
    if authorized(update, config):
        await update.effective_message.reply_text(
            f"연계 질문 모드입니다. 최근 대화 최대 {MAX_TURNS}쌍을 기억합니다.\n"
            "/new: 기억 초기화 | /status: 기억 상태 | /id: 내 ID\n"
            "봇을 재시작하면 기억이 사라집니다."
        )
    elif config["owner"] is None:
        await identify(update, context)


async def new_conversation(update, context):
    if not authorized(update, context.bot_data["config"]):
        return
    context.chat_data.pop("history", None)
    await update.effective_message.reply_text(
        "봇의 대화 기억을 비웠습니다. 새 주제로 질문하세요.\n"
        "텔레그램에 보이는 이전 메시지는 삭제하지 않습니다."
    )


async def status(update, context):
    if not authorized(update, context.bot_data["config"]):
        return
    history = context.chat_data.get("history", [])
    await update.effective_message.reply_text(
        f"기억 중: {len(history)}쌍 / 최대 {MAX_TURNS}쌍\n"
        f"기록 길이: {history_chars(history):,}자 / 최대 {MAX_HISTORY_CHARS:,}자\n"
        "메모리에만 보관합니다. /new 또는 재시작으로 비울 수 있습니다."
    )


async def ask_ai(config, messages, transport=None):
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(120.0, connect=5.0),
        trust_env=False,
        transport=transport,
    ) as client:
        response = await client.post(
            config["base"] + "/chat/completions",
            headers={"Authorization": "Bearer " + config["key"]},
            json={
                "model": config["model"],
                "messages": messages,
                "max_tokens": 768,
                "stream": False,
            },
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Empty AI response")
        return answer.strip()


async def reply(update, context):
    config = context.bot_data["config"]
    if not authorized(update, config):
        return
    message = update.effective_message
    if len(message.text) > MAX_INPUT_CHARS:
        await message.reply_text(f"질문을 {MAX_INPUT_CHARS:,}자 이하로 줄여 주세요.")
        return
    history = context.chat_data.get("history", [])
    messages = build_messages(history, message.text)
    await message.reply_text("이전 대화를 참고해 답변을 준비하고 있습니다.")
    try:
        answer = await asyncio.wait_for(ask_ai(config, messages), timeout=150)
    except httpx.HTTPStatusError as exc:
        await message.reply_text(
            f"FreeLLMAPI HTTP {exc.response.status_code}: 키·모델·한도를 확인하세요.\n"
            "문맥 길이 오류라면 /new로 기억을 비운 뒤 다시 질문하세요."
        )
        return
    except (httpx.TimeoutException, asyncio.TimeoutError):
        await message.reply_text("AI 응답 시간이 초과됐습니다. 잠시 뒤 다시 질문하세요.")
        return
    except httpx.RequestError:
        await message.reply_text("FreeLLMAPI에 연결할 수 없습니다. 앱 실행 상태와 주소를 확인하세요.")
        return
    except (ValueError, KeyError, IndexError, TypeError):
        await message.reply_text("AI 답변 형식을 확인할 수 없습니다. 다른 모델을 시도하세요.")
        return
    for start in range(0, len(answer), 1500):
        await message.reply_text(answer[start : start + 1500])
        await asyncio.sleep(0.2)
    # Save only after inference and delivery have both succeeded.
    context.chat_data["history"] = trim_history(history + [(message.text, answer)])


async def on_error(update, context):
    # URLs in raw exception messages may contain the Telegram bot token.
    print(f"텔레그램 처리 오류: {type(context.error).__name__}", flush=True)


def build_application(config):
    app = Application.builder().token(config["token"]).concurrent_updates(False).build()
    app.bot_data["config"] = config
    app.add_handler(CommandHandler("start", welcome))
    app.add_handler(CommandHandler("id", identify))
    app.add_handler(CommandHandler("new", new_conversation))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    app.add_error_handler(on_error)
    return app


def main():
    logging.basicConfig(level=logging.CRITICAL)
    config = settings()
    app = build_application(config)
    mode = "연계 질문 모드" if config["owner"] else "ID 확인 모드: 텔레그램에서 /id를 보내세요."
    print(f"{mode} | 종료: Ctrl+C", flush=True)
    app.run_polling(allowed_updates=["message"], drop_pending_updates=True)


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"설정 오류: {exc}")
        raise SystemExit(1) from None
    except Exception as exc:
        print(f"시작 오류: {type(exc).__name__}. 봇 토큰·인터넷·중복 실행을 확인하세요.")
        raise SystemExit(1) from None
