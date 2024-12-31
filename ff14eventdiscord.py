import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import requests
from lxml import html, etree
import logging
import asyncio

# 디스코드 봇 토큰
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
BASE_URL = 'https://www.ff14.co.kr'
EVENT_URL_TEMPLATE = 'https://www.ff14.co.kr/news/event?category=1&page={}'

# 서버 ID를 저장할 사전
guild_ids = {}

# 봇 초기화
intents = discord.Intents.default()
intents.message_content = True  # 메시지 읽기 활성화
bot = commands.Bot(command_prefix="!", intents=intents)
logging.basicConfig(level=logging.INFO)

@bot.event
async def on_ready():
    print(f"{bot.user}로 로그인되었습니다!")
    await bot.tree.sync()  # 슬래시 명령어 동기화
    print("슬래시 명령어가 동기화되었습니다.")
    check_events.start()  # 이벤트 확인 작업 시작

@tasks.loop(hours=5)
async def check_events():
    print("이벤트를 확인하고 있습니다...")

    try:
        for guild_id in guild_ids.values():
            guild = bot.get_guild(guild_id)
            if guild is None:
                print(f"서버를 찾을 수 없습니다. GUILD_ID: {guild_id}")
                continue

            # 서버에서 기존 이벤트 목록 가져오기
            existing_events = await guild.fetch_scheduled_events()
            existing_event_titles = [event.name for event in existing_events]

            for page in range(1, 4):  # 1페이지부터 3페이지까지 순회
                event_url = EVENT_URL_TEMPLATE.format(page)
                # 웹 페이지에서 이벤트 정보 가져오기
                response = requests.get(event_url)
                if response.status_code != 200:
                    print(f"이벤트 페이지를 불러오는 데 실패했습니다. URL: {event_url}")
                    continue
                
                tree = html.fromstring(response.text)
                
                # 필요한 범위의 요소들 가져오기
                event_elements = tree.xpath('/html/body/div/div/div/div/div/ul/li/a')
                if not event_elements:
                    print("이벤트 정보를 찾을 수 없습니다.")
                    continue
                
                for event in event_elements:
                    # 이벤트 제목
                    event_title = event.xpath('span[2]/span[1]/span[1]/child::node()')
                    if not event_title:
                        continue
                    event_title = str(event_title[0]).strip()

                    # 이미 존재하는 이벤트인지 확인
                    if event_title in existing_event_titles:
                        print(f"이미 존재하는 이벤트: {event_title}")
                        continue
                    
                    # 이벤트 링크
                    event_link = event.xpath('span[2]/span[1]/span[1]/ancestor-or-self::node()/@href')
                    if not event_link:
                        continue
                    full_event_link = BASE_URL + str(event_link[0]).split('?')[0]  # `?` 이후의 부분 제거
                    
                    # 이벤트 설명
                    event_description_nodes = event.xpath('span[2]/span[3]/child::node()')
                    if not event_description_nodes:
                        continue
                    event_description = ' '.join([str(node).strip() for node in event_description_nodes if isinstance(node, etree._ElementUnicodeResult)])
                    
                    # 이벤트 날짜
                    event_date = event.xpath('span[2]/span[2]//text()')
                    if not event_date:
                        continue
                    event_date = str(event_date[0]).strip()
                    
                    # 날짜 파싱
                    start_date_str, end_date_str = event_date.split(' ~ ')
                    start_date = datetime.strptime('20' + start_date_str, '%Y-%m-%d').astimezone()
                    end_date = datetime.strptime('20' + end_date_str, '%Y-%m-%d').astimezone()
                    
                    # 현재 시간 기준으로 설정
                    now = datetime.now().astimezone()
                    if start_date < now:
                        start_date = now + timedelta(minutes=1)
                    if end_date < now:
                        end_date = start_date + timedelta(hours=1)

                    # 로그에 정보 출력
                    logging.info(f"이벤트 제목: {event_title}, 링크: {full_event_link}, 설명: {event_description}, 시작 날짜: {start_date}, 종료 날짜: {end_date}")

                    # 이벤트 생성
                    event = await guild.create_scheduled_event(
                        name=event_title,
                        description=event_description,
                        start_time=start_date,
                        end_time=end_date,
                        entity_type=discord.EntityType.external,
                        location=full_event_link,  # 이벤트의 위치를 링크로 설정
                        privacy_level=discord.PrivacyLevel.guild_only
                    )

                    print(f"이벤트 생성 성공: {event.name} (ID: {event.id})")
        
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)

@bot.tree.command(name="이벤트생성", description="FF14 이벤트를 수동으로 생성합니다.")
async def create_event(interaction: discord.Interaction):
    await check_events()
    await interaction.response.send_message("이벤트가 확인되고 생성되었습니다.", ephemeral=True)

@bot.tree.command(name="이벤트종료", description="서버에 등록된 모든 이벤트를 종료합니다.")
async def cancel_events(interaction: discord.Interaction):
    try:
        guild = bot.get_guild(interaction.guild_id)
        if guild is None:
            await interaction.response.send_message("서버를 찾을 수 없습니다. 관리자에게 문의하세요.", ephemeral=True)
            return

        # 서버에서 기존 이벤트 목록 가져오기
        existing_events = await guild.fetch_scheduled_events()
        
        for event in existing_events:
            await event.delete()
            print(f"이벤트 종료 성공: {event.name} (ID: {event.id})")

        await interaction.response.send_message("모든 이벤트가 종료되었습니다.", ephemeral=True)

    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        await interaction.response.send_message(f"이벤트 종료 중 문제가 발생했습니다: {e}", ephemeral=True)

@bot.tree.command(name="서버등록", description="서버를 이벤트 관리 목록에 추가합니다.")
async def register_server(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    guild_ids[guild_id] = guild_id
    await interaction.response.send_message(f"서버가 등록되었습니다. GUILD_ID: {guild_id}", ephemeral=True)

bot.run(TOKEN)
