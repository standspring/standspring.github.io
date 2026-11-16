import os

from openai import OpenAI


def main():
    api_key = os.environ.get("FREELLMAPI_API_KEY")
    if not api_key:
        raise SystemExit("FREELLMAPI_API_KEY 환경 변수를 먼저 설정하세요.")

    with OpenAI(
        base_url=os.environ.get(
            "FREELLMAPI_BASE_URL", "http://localhost:3001/v1"
        ),
        api_key=api_key,
        timeout=90.0,
        max_retries=0,
    ) as client:
        raw_response = client.chat.completions.with_raw_response.create(
            model=os.environ.get("FREELLMAPI_MODEL", "auto"),
            messages=[
                {"role": "user", "content": "파이썬 리스트와 튜플의 차이를 간단히 알려 줘."}
            ],
            max_tokens=400,
        )
        response = raw_response.parse()
        print(response.choices[0].message.content or "텍스트 응답이 없습니다.")
        print("실제 처리 경로:", raw_response.headers.get("x-routed-via", "미제공"))
        print("대체 시도:", raw_response.headers.get("x-fallback-attempts", "미제공"))
        if response.usage is not None:
            print("보고된 사용량:", response.usage.model_dump())


if __name__ == "__main__":
    main()
