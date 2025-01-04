# Discord Event Manager Bot

이 디스코드 봇은 Final Fantasy XIV (FF14) 이벤트를 관리하는 데 도움을 줍니다. 봇은 이벤트를 생성하고, 선택하며, 취소하는 기능을 제공합니다.

## 기능

- **이벤트 생성**: FF14 웹 페이지에서 이벤트를 가져와 디스코드 서버에 생성합니다.
- **이벤트 선택**: 사용자가 Select 메뉴를 통해 이벤트를 선택하고 생성할 수 있습니다.
- **이벤트 취소**: 디스코드 서버에 등록된 모든 이벤트를 취소합니다.

## 설치 및 설정

1. 저장소를 클론합니다:
    ```sh
    git clone https://github.com/yourusername/discord-event-manager-bot.git
    cd discord-event-manager-bot
    ```

2. 필요한 패키지를 설치합니다:
    ```sh
    pip install -r requirements.txt
    ```

3. `.env` 파일을 생성하고 디스코드 봇 토큰을 설정합니다:
    ```plaintext
    DISCORD_BOT_TOKEN=your_discord_bot_token
    ```

## 사용 방법

1. 봇을 실행합니다:
    ```sh
    python bot.py
    ```

2. 디스코드 서버에서 봇을 사용해 이벤트를 관리합니다:
    - `/이벤트생성`: FF14 이벤트를 수동으로 생성합니다.
    - `/이벤트종료`: 서버에 등록된 모든 이벤트를 종료합니다.
    - `/이벤트선택`: Select Menus를 사용하여 이벤트를 선택하고 생성합니다.

## 기여

기여를 원하신다면, [기여 가이드라인](CONTRIBUTING.md)을 읽어주세요.

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)에 따라 라이선스가 부여됩니다.

## 문의

궁금한 사항이 있으면 [이슈](https://github.com/yourusername/discord-event-manager-bot/issues)를 통해 문의해 주세요.
