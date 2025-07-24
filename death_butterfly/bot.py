import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드

# 환경 변수 불러오기
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
INTRO_CHANNEL_ID = os.getenv("INTRO_CHANNEL_ID")
CHANNEL2 = os.getenv("CHANNEL2")
SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY2 = os.getenv("SECRET_KEY2")

# 필수 환경변수 확인
if not INTRO_CHANNEL_ID or not CHANNEL2:
    raise ValueError("❗ INTRO_CHANNEL_ID 또는 CHANNEL2가 .env에 설정되지 않았습니다.")
INTRO_CHANNEL_ID = int(INTRO_CHANNEL_ID)
CHANNEL2 = int(CHANNEL2)

# 역할 이름
KEY_ROLE_NAME = "Key"
SECRET_ROLE_NAME = "출입증"
MINOR_ROLE_NAME = "미성년자"
ADULT_ROLE_NAME = "성인"
MALE_ROLE_NAME = "남자"
FEMALE_ROLE_NAME = "여자"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# 인사말 파싱
def parse_intro(message):
    content = message.content
    name = age = gender = source = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("이름:"):
            name = line[3:].strip()
        elif line.startswith("나이:"):
            age = line[3:].strip()
        elif line.startswith("성별:"):
            gender = line[3:].strip()
        elif line.startswith("유입:"):
            source = line[3:].strip()
    return name, age, gender, source

@bot.event
async def on_ready():
    print(f"{bot.user} 로 로그인됨")

@bot.event
async def on_message(message):
    global SECRET_KEY, SECRET_KEY2
    if message.author.bot:
        return

    if message.channel.id == INTRO_CHANNEL_ID:
        name, age, gender, source = parse_intro(message)
        if not all([name, age, gender, source]):
            await message.channel.send("❗ 인사 양식이 올바르지 않습니다.")
            return

        try:
            age = int(age)
        except ValueError:
            await message.channel.send("❗ 나이는 숫자로 입력해주세요.")
            return

        # 닉네임 변경
        try:
            await message.author.edit(nick=name)
        except discord.Forbidden:
            await message.channel.send("⚠️ 닉네임을 변경할 권한이 없습니다.")

        # 역할 부여
        role_names = []
        if age >= 7:
            role_names.append(MINOR_ROLE_NAME)
        else:
            role_names.append(ADULT_ROLE_NAME)

        if gender.startswith("여") or gender.startswith("ㅇ"):
            role_names.append(FEMALE_ROLE_NAME)
        elif gender.startswith("남") or gender.startswith("ㄴ"):
            role_names.append(MALE_ROLE_NAME)

        roles = [discord.utils.get(message.guild.roles, name=r) for r in role_names if r]
        await message.author.add_roles(*[r for r in roles if r])

        await message.channel.send(f"✅ 역할이 부여되었습니다: {', '.join(role_names)}")

    await bot.process_commands(message)

# 출입증 명령어 (지정 채널만)
@bot.command(name="출입증")
async def 출입증(ctx, 입력된키: str):
    global SECRET_KEY
    if ctx.channel.id != CHANNEL2:
        return await ctx.send("❗ 이 명령어는 지정된 채널에서만 사용할 수 있습니다.")
    if SECRET_KEY is None:
        return await ctx.send("⚠️ 출입증 키가 설정되지 않았습니다.")
    if 입력된키 == SECRET_KEY:
        key_role = discord.utils.get(ctx.guild.roles, name=KEY_ROLE_NAME)
        secret_role = discord.utils.get(ctx.guild.roles, name=SECRET_ROLE_NAME)

        if key_role in ctx.author.roles:
            await ctx.author.remove_roles(key_role)

        if secret_role:
            await ctx.author.add_roles(secret_role)
            return await ctx.send("🔓 출입증 역할이 부여되었습니다.")
        else:
            return await ctx.send("❗ 출입증 역할이 서버에 존재하지 않습니다.")
    else:
        return await ctx.send("❌ 잘못된 키입니다.")

# 인증 키 설정 (관리자만)
@bot.command(name="인증키")
@commands.has_permissions(administrator=True)
async def 인증키설정(ctx, new_key: str):
    global SECRET_KEY2
    SECRET_KEY2 = new_key
    await ctx.send("✅ 인증 키가 설정되었습니다.")

# 출입증 키 설정 (관리자만)
@bot.command(name="출입증설정")
@commands.has_permissions(administrator=True)
async def 출입증설정(ctx, new_key: str):
    global SECRET_KEY
    SECRET_KEY = new_key
    await ctx.send("✅ 출입증 키가 설정되었습니다.")

# 봇 인증 (관리자만)
@bot.command(name="인증")
@commands.has_permissions(administrator=True)
async def 인증(ctx, key: str):
    global SECRET_KEY2
    if SECRET_KEY2 is None:
        return await ctx.send("❗ 인증 키가 설정되지 않았습니다.")
    if key == SECRET_KEY2:
        await ctx.send("✅ 봇이 성공적으로 인증되었습니다.")
    else:
        await ctx.send("❌ 잘못된 인증 키입니다.")

# 상태 확인 (관리자만)
@bot.command(name="상태")
@commands.has_permissions(administrator=True)
async def 상태(ctx):
    global SECRET_KEY, SECRET_KEY2
    status = f"""🔐 **현재 상태**
- 출입증 키 설정됨: {'✅' if SECRET_KEY else '❌'}
- 인증 키 설정됨: {'✅' if SECRET_KEY2 else '❌'}
"""
    await ctx.send(status)

# 봇 실행
bot.run(DISCORD_TOKEN)
