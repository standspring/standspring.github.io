"""Personal Telegram -> FreeLLMAPI bridge. Each question is independent."""

import asyncio
import logging
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters


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
        "base": os.getenv("FREELLMAPI_BASE_URL", "http://127.0.0.1:3001/v1").rstrip("/"),
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


async def identify(update, context):
    # /id only reports the sender's own ID; it never calls an AI service.
    if update.effective_chat and update.effective_chat.type == "private":
        await update.effective_message.reply_text(
            f"내 사용자 ID: {update.effective_user.id}\n"
            "이 숫자를 .env의 ALLOWED_TELEGRAM_USER_ID에 넣고 봇을 재시작하세요."
        )


async def welcome(update, context):
    config = context.bot_data["config"]
    if authorized(update, config):
        await update.effective_message.reply_text(
            "연결 준비가 됐습니다. 질문을 보내세요. 각 질문은 별도로 처리합니다."
        )
    elif config["owner"] is None:
        await identify(update, context)


async def ask_ai(config, text, transport=None):
    # Disable environment proxies only for this local FreeLLMAPI connection.
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
                "messages": [
                    {"role": "system", "content": "한국어로 이해하기 쉽게 답하세요."},
                    {"role": "user", "content": text},
                ],
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
    if len(message.text) > 4000:
        await message.reply_text("질문을 4,000자 이하로 줄여 주세요.")
        return
    await message.reply_text("답변을 준비하고 있습니다.")
    try:
        # Overall deadline also covers a server that keeps sending tiny chunks.
        answer = await asyncio.wait_for(ask_ai(config, message.text), timeout=150)
    except httpx.HTTPStatusError as exc:
        await message.reply_text(
            f"FreeLLMAPI HTTP {exc.response.status_code}: 통합 키·모델·한도를 확인하세요."
        )
        return
    except (httpx.TimeoutException, TimeoutError):
        await message.reply_text("AI 응답 시간이 초과됐습니다. 잠시 뒤 새로 질문하세요.")
        return
    except httpx.RequestError:
        await message.reply_text("FreeLLMAPI에 연결할 수 없습니다. 앱 실행 상태와 주소를 확인하세요.")
        return
    except (ValueError, KeyError, IndexError, TypeError):
        await message.reply_text("AI 답변 형식을 확인할 수 없습니다. 다른 모델을 시도하세요.")
        return
    # 1,500 Unicode code points fit even when every character uses two UTF-16 units.
    for start in range(0, len(answer), 1500):
        await message.reply_text(answer[start : start + 1500])
        await asyncio.sleep(0.2)


async def on_error(update, context):
    # Do not print raw exceptions: request URLs may contain the Telegram token.
    print(f"텔레그램 처리 오류: {type(context.error).__name__}", flush=True)


def main():
    logging.basicConfig(level=logging.CRITICAL)
    config = settings()
    app = Application.builder().token(config["token"]).build()
    app.bot_data["config"] = config
    app.add_handler(CommandHandler("start", welcome))
    app.add_handler(CommandHandler("id", identify))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    app.add_error_handler(on_error)
    mode = "AI 질문 모드" if config["owner"] else "ID 확인 모드: 텔레그램에서 /id를 보내세요."
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
