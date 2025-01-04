import discord
from discord.ext import commands
import logging
from bot_functions import create_event, cancel_events, select_events, set_bot, on_select_interaction

# 디스코드 봇 토큰
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'

# 봇 초기화
intents = discord.Intents.default()
intents.message_content = True  # 메시지 읽기 활성화
bot = commands.Bot(command_prefix="!", intents=intents)
logging.basicConfig(level=logging.INFO)

# bot 객체를 bot_functions 모듈로 전달
set_bot(bot)

@bot.event
async def on_ready():
    print(f"{bot.user}로 로그인되었습니다!")
    await bot.tree.sync()  # 슬래시 명령어 동기화
    print("슬래시 명령어가 동기화되었습니다.")

bot.tree.command(name="이벤트생성", description="FF14 이벤트를 수동으로 생성합니다.")(create_event)
bot.tree.command(name="이벤트종료", description="서버에 등록된 모든 이벤트를 종료합니다.")(cancel_events)
bot.tree.command(name="이벤트선택", description="Select Menus를 사용하여 이벤트를 선택하고 생성합니다.")(select_events)

# bot 객체 설정 후 이벤트 핸들러 등록
@bot.event
async def on_interaction(interaction: discord.Interaction):
    await on_select_interaction(interaction)

bot.run(TOKEN)
