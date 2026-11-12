import os
import re

import requests

BASE_URL = "https://openapi.imeritz.com:9443"


def read_json(response):
    try:
        body = response.json()
    except ValueError:
        raise RuntimeError(f"JSON 응답이 아닙니다: HTTP {response.status_code}") from None
    if not isinstance(body, dict):
        raise RuntimeError("예상한 JSON 객체가 아닙니다.")
    return body


def failure(response, body):
    # 전체 응답·헤더·토큰 대신 오류 진단에 필요한 필드만 표시한다.
    return RuntimeError(
        f"HTTP {response.status_code}, "
        f"rsp_cd={body.get('rsp_cd')!r}, "
        f"rsp_msg={body.get('rsp_msg')!r}, "
        f"rsp_sub_msg={body.get('rsp_sub_msg')!r}"
    )


def main():
    app_key = os.environ["MERITZ_APP_KEY"]
    app_secret = os.environ["MERITZ_APP_SECRET"]
    mac = os.environ["MERITZ_MAC_ADDRESS"]
    if not re.fullmatch(r"[0-9A-F]{12}", mac):
        raise ValueError("MAC 주소는 구분자 없는 12자리 대문자 16진수여야 합니다.")

    with requests.Session() as session:
        response = session.post(
            f"{BASE_URL}/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": app_key,
                "client_secret": app_secret,
                "scope": "login",
            },
            timeout=15,
        )
        body = read_json(response)
        token = body.get("access_token")
        if response.status_code != 200 or not token:
            raise failure(response, body)
        print("토큰 발급 완료, 유효기간(초):", body.get("expires_in"))

        response = session.get(
            f"{BASE_URL}/market/v1/prices",
            headers={
                "authorization": f"Bearer {token}",
                "mac_address": mac,
            },
            params={"mrkt_div_code": "J", "iscd": "005930"},
            timeout=15,
        )
        body = read_json(response)
        # 현재가 API의 성공 코드만 판정한다. 다른 API에 일반화하지 않는다.
        if response.status_code != 200 or body.get("rsp_cd") != "0000":
            raise failure(response, body)
        quote = body.get("data")
        if not isinstance(quote, dict) or quote.get("shrn_iscd") != "005930":
            raise RuntimeError("응답 종목코드를 확인할 수 없습니다.")
        if not quote.get("kor_isnm") or not quote.get("stck_prpr"):
            raise RuntimeError("종목명·현재가가 비어 있습니다. 요청과 장 상태를 확인하세요.")
        print("종목명:", quote["kor_isnm"])
        print("현재가:", quote["stck_prpr"])
        print("누적거래량:", quote.get("acml_vol"))


if __name__ == "__main__":
    main()
