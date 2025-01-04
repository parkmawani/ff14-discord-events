from datetime import datetime, timedelta
import aiohttp
from lxml import html, etree
import re
import logging
import discord

BASE_URL = 'https://www.ff14.co.kr'
EVENT_URL_TEMPLATE = 'https://www.ff14.co.kr/news/event?category=1&page={}'

bot = None

def set_bot(bot_instance):
    global bot
    bot = bot_instance

class EventSelectView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Select(
            placeholder="이벤트를 선택하세요...",
            options=options,
            custom_id="select_event"
        ))

async def select_events(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)  # 인터랙션을 연장

    guild = bot.get_guild(interaction.guild_id)
    if guild is None:
        await interaction.followup.send("서버를 찾을 수 없습니다. 관리자에게 문의하세요.", ephemeral=True)
        return

    # 서버에서 기존 이벤트 목록 가져오기
    existing_events = await guild.fetch_scheduled_events()
    existing_event_titles = [event.name for event in existing_events]

    # 웹 페이지에서 이벤트 정보 가져오기
    event_options = []
    async with aiohttp.ClientSession() as session:
        async with session.get(EVENT_URL_TEMPLATE.format(1)) as response:
            if response.status != 200:
                await interaction.followup.send("이벤트 페이지를 불러오는 데 실패했습니다.", ephemeral=True)
                return
            
            text = await response.text()
            tree = html.fromstring(text)
            event_elements = tree.xpath('/html/body/div/div/div/div/div/ul/li/a')
            for event in event_elements:
                event_title = event.xpath('span[2]/span[1]/span[1]/child::node()')
                if not event_title:
                    continue
                event_title = str(event_title[0]).strip()

                if event_title not in existing_event_titles:
                    event_options.append(discord.SelectOption(label=event_title, value=event_title))

    # 선택 메뉴 생성 및 view 추가
    view = EventSelectView(event_options)

    await interaction.followup.send("생성할 이벤트를 선택하세요:", view=view, ephemeral=True)

async def on_select_interaction(interaction: discord.Interaction):
    if interaction.data.get("custom_id") == "select_event":
        await interaction.response.defer(ephemeral=True)  # 인터랙션을 연장

        selected_events = interaction.data.get("values", [])
        guild = bot.get_guild(interaction.guild_id)

        async with aiohttp.ClientSession() as session:
            async with session.get(EVENT_URL_TEMPLATE.format(1)) as response:
                if response.status != 200:
                    await interaction.followup.send("이벤트 페이지를 불러오는 데 실패했습니다.", ephemeral=True)
                    return
                
                text = await response.text()
                tree = html.fromstring(text)
                event_elements = tree.xpath('/html/body/div/div/div/div/div/ul/li/a')
                for event in event_elements:
                    title = event.xpath('span[2]/span[1]/span[1]/child::node()')
                    if not title:
                        continue
                    event_title = str(title[0]).strip()
                    
                    if event_title not in selected_events:
                        continue

                    full_event_link = BASE_URL + str(event.xpath('span[2]/span[1]/span[1]/ancestor-or-self::node()/@href')[0]).split('?')[0]
                    event_description = ' '.join([str(node).strip() for node in event.xpath('span[2]/span[3]/child::node()') if isinstance(node, etree._ElementUnicodeResult)])
                    event_date = str(event.xpath('span[2]/span[2]//text()')[0]).strip()
                    start_date_str, end_date_str = event_date.split(' ~ ')
                    start_date = datetime.strptime('20' + start_date_str, '%Y-%m-%d').astimezone()
                    end_date = datetime.strptime('20' + end_date_str, '%Y-%m-%d').astimezone()
                    
                    now = datetime.now().astimezone()
                    if start_date < now:
                        start_date = now + timedelta(minutes=1)
                    if end_date < now:
                        end_date = start_date + timedelta(hours=1)

                    event_cover_style = event.xpath('span[1]/span[1]/@style')
                    event_cover_url = None
                    if event_cover_style:
                        style = event_cover_style[0]
                        match = re.search(r"url\('?(.*?)'?\)", style)
                        if match:
                            event_cover_url = match.group(1)
                        if event_cover_url and event_cover_url.startswith('//'):
                            event_cover_url = 'https:' + event_cover_url

                    logging.info(f"이벤트 제목: {event_title}, 링크: {full_event_link}, 설명: {event_description}, 시작 날짜: {start_date}, 종료 날짜: {end_date}")

                    event = await guild.create_scheduled_event(
                        name=event_title,
                        description=event_description,
                        start_time=start_date,
                        end_time=end_date,
                        entity_type=discord.EntityType.external,
                        location=full_event_link,
                        privacy_level=discord.PrivacyLevel.guild_only
                    )

                    if event_cover_url:
                        async with aiohttp.ClientSession() as image_session:
                            async with image_session.get(event_cover_url) as image_response:
                                if image_response.status == 200:
                                    image_data = await image_response.read()
                                    await event.edit(image=image_data)

                    print(f"이벤트 생성 성공: {event.name} (ID: {event.id})")

        await interaction.followup.send("선택된 이벤트가 생성되었습니다.", ephemeral=True)

async def create_event(interaction: discord.Interaction):
    await interaction.response.send_message("이벤트가 확인되고 생성되었습니다.", ephemeral=True)

async def cancel_events(interaction: discord.Interaction):
    try:
        guild = bot.get_guild(interaction.guild_id)
        if guild is None:
            await interaction.response.send_message("서버를 찾을 수 없습니다. 관리자에게 문의하세요.", ephemeral=True)
            return

        existing_events = await guild.fetch_scheduled_events()
        
        for event in existing_events:
            await event.delete()
            print(f"이벤트 종료 성공: {event.name} (ID: {event.id})")

        await interaction.response.send_message("모든 이벤트가 종료되었습니다.", ephemeral=True)

    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        await interaction.response.send_message(f"이벤트 종료 중 문제가 발생했습니다: {e}", ephemeral=True)
