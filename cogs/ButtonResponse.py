import os
import sys
if __name__ == "__main__":
    os.chdir(".")
    sys.path.append(os.getcwd())
    
    # main.pyを実行
    os.system(f"{sys.executable} main.py")
    
import discord
import re
import asyncio
from discord.ext import commands
from Database import Database
from UI.Support import PremiseSelectMenu

THREAD_LIMIT = 1000

class ButtonResponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Database("config.json")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2: # 応答がボタンであれば
                await interaction.response.defer()

                if interaction.data["custom_id"] == "purchase_ok":
                    await self.send_purchase_ok(interaction)

                elif interaction.data["custom_id"] == "purchase_cancel":
                    await self.send_purchase_cancel(interaction)
                elif interaction.data["custom_id"] == "support_completion":
                    await self.close_thread(interaction)
                elif interaction.data["custom_id"] == "support_delete":
                    await self.delete_thread(interaction)

                else:
                    # ボタンの情報を取得する
                    buttons = self.config.get_value(interaction.guild_id, "support", "privates", default_value=[])
                    button_data: dict = next((item for item in buttons if item["id"] == interaction.data["custom_id"]), None)
                    if button_data:
                        await self.context_switcher(interaction, button_data)
        except:
            pass

    async def context_switcher(self, interaction: discord.Interaction, button_data: dict):
        # フォーマットが書かれていなければ終了
        if not "format" in button_data.keys():
            return
        # セレクトメニューがなければ終了
        if not ("select_menu" in button_data.keys() and "title" in button_data.keys()):
            return

        if button_data["format"] == "forum":
            await self.send_forum_message(interaction, button_data)
        elif button_data["format"] == "purchase":
            await self.send_purchase_message(interaction, button_data)

    async def send_forum_message(self, interaction: discord.Interaction, button_data: dict):
        if self.is_supportable(interaction, button_data):
            await interaction.followup.send("お問い合わせありがとうございます。\nこちらのメッセージは自動送信です。あなたにのみ表示されており、時間経過で削除されます。\n\n対応をスムーズに行うためにお問い合わせ内容(カテゴリ)の選択と、カテゴリ選択後に表示されるフォーラムのタイトル入力を適切に行ってください。\nフォーラムを送信すると担当者が交代して対応いたします。\n対応までに時間がかかる場合がございますがご了承ください。", ephemeral=True, view=PremiseSelectMenu(button_data, "forum"))

    async def send_purchase_message(self, interaction: discord.Interaction, button_data: dict):
        if self.is_supportable(interaction, button_data):
            await interaction.followup.send("ご利用ありがとうございます。\nこちらのメッセージは自動送信です。あなたにのみ表示されており、時間経過で削除されます。\n購入手続きは運営が順を追って対応いたします。\n\n購入する内容(カテゴリ)の選択をすると運営とのプライベートチャットが開かれます。\nカテゴリの選択後、決定ボタンを押すことで購入内容が確定されます。", ephemeral=True, view=PremiseSelectMenu(button_data, "purchase"))

    async def is_supportable(self, interaction: discord.Interaction, button_data: dict) -> bool:
        actice_threads = await interaction.guild.active_threads()
        if len(len(actice_threads)) < THREAD_LIMIT:
            return False

        await interaction.followup.send("現在、お問い合わせのプライベートチャットが大変込み合っています。しばらく待ってからもう一度お試しください。", ephemeral=True)
        
        operate_ch = self.config.get_value(interaction.guild_id, "support", "alarm_channel")
        if not operate_ch:
            return
        
        notice_ch = interaction.guild.get_channel(operate_ch)
        notice_ch.send("## お問い合わせが飽和しています。\n解決したお問い合わせチャットをアーカイブ化してください。")

    async def send_purchase_ok(self, interaction: discord.Interaction):
        await interaction.edit_original_response(content=interaction.message.content, view=None)
        await interaction.followup.send("ありがとうございます。\n担当者が対応いたします。しばらくお待ちください。")

        # 利用数を記録
        count = self.config.get_value(interaction.guild_id, "support", "used_count", default_value=0)
        count += 1
        self.config.set_value(interaction.guild_id, "support", "used_count", value=count)

        # 運営用に通知
        operate_ch = self.config.get_value(interaction.guild_id, "support", "alarm_channel")
        if not operate_ch:
            return
        
        # 完了ボタン
        completion_button = discord.ui.Button(label="完了", style=discord.ButtonStyle.success, custom_id="support_completion")
        view = discord.ui.View()
        view.add_item(completion_button)

        notice_ch = interaction.guild.get_channel(operate_ch)
        await notice_ch.send(f"## 新しい購入手続きがあります\n購入者: {interaction.user.mention}\n{interaction.channel.jump_url}\nid:`{interaction.channel.id}`", view=view)

    async def send_purchase_cancel(self, interaction: discord.Interaction):
        await interaction.channel.delete()

    async def close_thread(self, interaction: discord.Interaction):
        # 押されたボタンから対象のスレッドを取得
        pattern = r"\`(.*?)\`"
        matches = re.findall(pattern, interaction.message.content)
        completion_thread = interaction.guild.get_thread(int(matches[0]))

        if completion_thread:
            # スレッドが存在すればスレッドを閉じる
            await completion_thread.edit(archived=True)
            # 削除ボタン追加
            completion_button = discord.ui.Button(label="完了", style=discord.ButtonStyle.success, disabled=True)
            delete_button = discord.ui.Button(label="削除", style=discord.ButtonStyle.danger, custom_id="support_delete")
            view = discord.ui.View()
            view.add_item(completion_button)
            view.add_item(delete_button)
            await interaction.edit_original_response(content=interaction.message.content, view=view)

    async def delete_thread(self, interaction: discord.Interaction):
        # 押されたボタンから対象のスレッドを取得
        pattern = r"\`(.*?)\`"
        matches = re.findall(pattern, interaction.message.content)
        completion_thread = await interaction.guild.fetch_channel(matches[0])

        if len(matches) == 1:
            # 1回目のボタンだったら再確認する
            original_text = interaction.message.content
            await interaction.edit_original_response(content=original_text + "\n`削除するにはもう一度押してください`")

            # 5秒の猶予
            await asyncio.sleep(5)

            # 削除取り消し
            await interaction.edit_original_response(content=original_text)
            return
        
        # 2回目以降は「`削除するにはもう一度押してください`」によりmatchesが2になるため削除する
        
        if completion_thread:
            # スレッドが存在すればスレッドを削除する
            await completion_thread.delete()
            
            # お知らせメッセージも削除
            await interaction.delete_original_response()

async def setup(bot):
    await bot.add_cog(ButtonResponse(bot))