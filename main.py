# 必要なライブラリをインポート
import discord
import os
import asyncio
import random
import time
from dotenv import load_dotenv
from discord.ext import commands

# .envファイルを読み込む
load_dotenv()

# Discordのインテントを設定
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.voice_states = True

# コマンドのプレフィックスを設定
bot = commands.Bot(command_prefix='!', intents=intents)

# VCに入っているメンバーとその入室時間を記録する辞書
vc_members = {}

# Botが起動したときのイベント
@bot.event
async def on_ready():
    """BotがDiscordにログインしたときに実行されます。"""
    print(f'ログインしました: {bot.user}')
    bot.loop.create_task(check_vc_time())

# VCの状態が変化したときのイベント
@bot.event
async def on_voice_state_update(member, before, after):
    """
    メンバーのボイスステータスが更新されたときに実行されます。
    VCへの入室・退出を検知し、時間を記録します。
    """
    # ユーザーがVCに参加したとき
    if before.channel is None and after.channel is not None:
        # BotがVCに接続していない場合、自動で接続する
        if bot.voice_clients == []:
            await after.channel.connect()
            print(f'{after.channel.name}に自動で接続しました。')

        # ターゲットユーザーであるか確認
        target_users = {
            'YourUsernameHere', # ここにDiscordのユーザー名を記述
        }
        if member.name in target_users:
            print(f'{member.name}がVCに参加しました。記録を開始します。')
            vc_members[member.id] = {'start_time': time.time(), 'sent_message': False}
    
    # ユーザーがVCから退出したとき
    if before.channel is not None and after.channel is None:
        if member.id in vc_members:
            del vc_members[member.id]
            print(f'{member.name}がVCから退出しました。記録を削除します。')

# 定期的にVCの滞在時間をチェックする非同期関数
async def check_vc_time():
    """VCの滞在時間を定期的にチェックし、メッセージを送信します。"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(60)

        current_time = time.time()
        members_to_notify = []

        for member_id, data in vc_members.items():
            start_time = data['start_time']
            sent_message = data['sent_message']
            if not sent_message and (current_time - start_time) > 30 * 60:
                members_to_notify.append(member_id)
                
        for member_id in members_to_notify:
            member = bot.get_user(member_id)
            if member:
                try:
                    await member.send(f'VCに30分以上いるみたいだよ。そろそろ勉強の時間じゃない？')
                    vc_members[member_id]['sent_message'] = True
                    print(f'{member.name}に30分以上経過のメッセージを送信しました。')
                except discord.Forbidden:
                    print(f'{member.name}にDMを送信できませんでした。')
    
# メッセージを受信したときのイベント
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if '勉強' in message.content:
        await message.channel.send('ゲーム作り頑張って！応援してるよ！')
    await bot.process_commands(message)

# VCから切断するコマンド
@bot.command()
async def disconnect(ctx):
    """BotをVCから切断させます。"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send('VCから切断しました。')
    else:
        await ctx.send('VCに接続していません。')

# Botの起動
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN is None:
    TOKEN = 'YOUR_BOT_TOKEN_HERE'

bot.run(TOKEN)