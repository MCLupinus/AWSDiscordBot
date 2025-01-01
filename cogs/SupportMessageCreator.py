import os
import sys
if __name__ == "__main__":
    os.chdir(".")
    sys.path.append(os.getcwd())
    
    # main.pyを実行
    os.system(f"{sys.executable} main.py")
    
import discord
import re
from discord import app_commands
from discord.ext import commands
from Database import Database
from datetime import datetime

REQUEST_MESSAGE = [
    "新しいフォーラムを作成します\nこの操作は全て最新のBOTメッセージをリプライしてください。\n\nフォーラムの説明を入力してください。",
    "フォーラムを開くボタンの名前を入力してください。",
    "フォーラムの名前を入力してください。",
    "カテゴリに必要な要素を入力してください。\n改行することで要素を分けることが可能です。\n一番上の行が最初に選択されている要素になります。",
    "送信するチャンネルを送信してください。\nこれを入力するとすぐに送信されます。"
]

class SupportMessageCreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_message: str = ""
        self.step: int = 0
        self.format = ""
        self.responses: list[str] = []
        self.config = Database("config.json")

    @app_commands.command(name="create_support", description="お問い合わせ用ボタンの設定を行います")
    @app_commands.describe(format="フォーラムの種類")
    @app_commands.choices(format=[
        discord.app_commands.Choice(name="フォーラム", value="forum"),
        discord.app_commands.Choice(name="購入", value="purchase")
    ])
    @commands.has_any_role('管理者', 'Discord対応')
    async def create_support(self, interaction: discord.Interaction, format: str):  
        if not self.last_message == "":
            await interaction.response.send_message("別の作業が進行中です。")
            return

        # 初期化
        self.step = 1
        self.responses.clear()

        self.format = format
        message = f"(1/{len(REQUEST_MESSAGE)})\n{REQUEST_MESSAGE[0]}"
        await interaction.response.send_message(message)
        self.last_message = message
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # BOTであれば無視
        if message.author == self.bot.user:
            return

        # 最新のメッセージをリプライしていたら保存して次のメッセージを送る
        if message.reference and message.reference.resolved:
            resolved = message.reference.resolved
            if resolved.content == self.last_message:
                if len(REQUEST_MESSAGE) <= self.step:
                    # 最後まで工程を終えたら作成する
                    await message.channel.send("必要な情報の入力が終わりました。")

                    # 送信チャンネルを取得
                    channel_mentions = re.findall(r"<#(\d+)>", message.content)
                    send_channel = message.guild.get_channel(int(channel_mentions[0]))
                    if not send_channel:
                        await message.channel.send("送信するチャンネルが無効もしくは見つかりません。")
                        return
                    
                    # ボタンを作成
                    id:str = f"{datetime.now().timestamp()}{message.author.id}"
                    button = discord.ui.Button(label=self.responses[1], style=discord.ButtonStyle.primary, custom_id=id)
                    view = discord.ui.View()
                    view.add_item(button)
                    # ボタン付きメッセージを送信
                    self.create_modal_data(id, message.guild.id)
                    await send_channel.send(self.responses[0], view=view)

                    # 終了
                    self.last_message = ""
                    return

                self.last_message = self.submit(message.content)  # 最終メッセージを更新
                await message.channel.send(self.last_message)
        
    def submit(self, message: str) -> str:
        self.responses.append(message)
        next_message = f"({self.step + 1}/{len(REQUEST_MESSAGE)})\n{REQUEST_MESSAGE[self.step]}"
        self.step += 1
        # 次のステップへ
        return next_message
    
    def create_modal_data(self, id: str, guild_id):
        data:list = self.config.get_value(guild_id, "support", "privates", default_value=[])
        data.append({
            "id": id,
            "format": self.format,
            "title": self.responses[2],
            "select_menu": self.responses[3].split("\n")
        })

        self.config.set_value(guild_id, "support", "privates", value=data)
        
async def setup(bot):
    await bot.add_cog(SupportMessageCreator(bot))