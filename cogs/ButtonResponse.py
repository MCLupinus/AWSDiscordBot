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

class SupportForum(discord.ui.Modal):
    def __init__(self, button_data:dict, select:str, select_message: discord.Interaction):
        super().__init__(title=f"お問い合わせ-{select}", timeout=None, custom_id=f"id{select}")
        self.button_data = button_data
        self.config = Database("config.json")
        self.select = select
        self.select_message = select_message
        self.support_title = discord.ui.TextInput(label="タイトル", style=discord.TextStyle.short, max_length=50)
        self.detail = discord.ui.TextInput(label="詳細", style=discord.TextStyle.paragraph)
        self.add_item(self.support_title)
        self.add_item(self.detail)

    async def on_submit(self, interaction: discord.Interaction):
        # セレクトメニューメッセージを削除
        await self.select_message.delete_original_response()
        title = f"【{self.select}】{self.support_title}"

        # 作成者が優先対応ロールを持っていたらタイトルに「優先」追加
        priority_roles = self.config.get_value(interaction.guild_id, "general", "priorities", default_value=[])

        for role in interaction.user.roles:
            if role.id in priority_roles:
                title = "【優先】" + title
                break

        await interaction.response.defer()
        thread = await interaction.channel.create_thread(
            name=title,
            invitable=False
        )
        await thread.add_user(interaction.user)

        # スレッドに最初の投稿を作成
        await thread.send(self.detail);
        
        # 利用数を記録
        count = self.config.get_value(interaction.guild_id, "support", "used_count", default_value=0)
        count += 1
        self.config.set_value(interaction.guild_id, "support", "used_count", value=count)

        # 作成したスレッドへ案内
        await self.select_message.followup.send(f"プライベートチャットを作成しました。: {thread.jump_url}\n運営の対応をお待ちください。",ephemeral=True)

        # 運営用に通知
        operate_ch = self.config.get_value(interaction.guild_id, "support", "alarm_channel")
        if not operate_ch:
            return
        
        # 完了ボタン
        completion_button = discord.ui.Button(label="完了", style=discord.ButtonStyle.success, custom_id="support_completion")
        view = discord.ui.View()
        view.add_item(completion_button)
        
        notice_ch = interaction.guild.get_channel(operate_ch)
        await notice_ch.send(f"## 新しいお問い合わせがあります\n{thread.jump_url}\nid:`{thread.id}`", view=view)

class PremiseSelectMenu(discord.ui.View):
    def __init__(self, button_data:dict, format:str):
        super().__init__(timeout=None)
        self.button_data = button_data
        self.selection = None
        self.format = format
        self.config = Database("config.json")

        self.add_item(self.premise_menu(button_data["select_menu"]))
        self.add_item(self.decision_button())

    def premise_menu(self, select_menu: list[str]) -> discord.ui.Select:
        options = []
        is_first = True
        for i in range(len(select_menu)):
            options.append(discord.SelectOption(label=select_menu[i], default=is_first))
            if is_first:
                self.selection = select_menu[0]
                is_first = False

        select = discord.ui.Select(placeholder="カテゴリを選択してください", options=options)
        select.callback = self.select_callback
        return select
    
    def decision_button(self) -> discord.ui.Button:
        button = discord.ui.Button(label="決定", style=discord.ButtonStyle.success)
        button.callback = self.quantity_button_callback
        return button
    
    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.selection = interaction.data["values"][0].title()

    async def quantity_button_callback(self, interaction: discord.Interaction):
        if self.format == "forum":
            # 入力フォーラムを表示
            await interaction.response.send_modal(SupportForum(self.button_data, self.selection, interaction))
        elif self.format == "purchase":
            # プライベートチャンネルを開く
            # セレクトメニューメッセージを削除
            await interaction.delete_original_response()
            title = str(self.selection)

            # 作成者が優先対応ロールを持っていたらタイトルに「優先」追加
            priority_roles = self.config.get_value(interaction.guild_id, "general", "priorities", default_value=[])

            for role in interaction.user.roles:
                if role.id in priority_roles:
                    title = "【優先】" + title
                    break

            thread = await interaction.channel.create_thread(
                name=title,
                invitable=False
            )
            await thread.add_user(interaction.user)

            # 作成したスレッドへ案内
            await interaction.followup.send(f"プライベートチャットを作成しました。\n{thread.jump_url}へ移動してください。",ephemeral=True)

            # スレッド内メッセージに表示するボタンを追加
            ok_button = discord.ui.Button(label="はい", style=discord.ButtonStyle.success, custom_id="purchase_ok")
            cancel_button = discord.ui.Button(label="取り消す", style=discord.ButtonStyle.secondary, custom_id="purchase_cancel")
            view = discord.ui.View()
            view.add_item(ok_button)
            view.add_item(cancel_button)
            
            # スレッドに最初の投稿を作成
            await thread.send(f"支援ありがとうございます。選択された内容は[**{self.selection}**]でお間違いありませんか？\n「はい」を押すまで手続きは進行しません。", view=view)

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
        await interaction.followup.send("お問い合わせありがとうございます。\nこちらのメッセージは自動送信です。あなたにのみ表示されており、時間経過で削除されます。\n\n対応をスムーズに行うためにお問い合わせ内容(カテゴリ)の選択と、カテゴリ選択後に表示されるフォーラムのタイトル入力を適切に行ってください。\nフォーラムを送信すると担当者が交代して対応いたします。\n対応までに時間がかかる場合がございますがご了承ください。", ephemeral=True, view=PremiseSelectMenu(button_data, "forum"))

    async def send_purchase_message(self, interaction: discord.Interaction, button_data: dict):
        await interaction.followup.send("ご利用ありがとうございます。\nこちらのメッセージは自動送信です。あなたにのみ表示されており、時間経過で削除されます。\n購入手続きは運営が順を追って対応いたします。\n\n購入する内容(カテゴリ)の選択をすると運営とのプライベートチャットが開かれます。\nカテゴリの選択後、決定ボタンを押すことで購入内容が確定されます。", ephemeral=True, view=PremiseSelectMenu(button_data, "purchase"))

    async def send_purchase_ok(self, interaction: discord.Interaction):
        await interaction.edit_original_response(content=interaction.message.content, view=None)
        await interaction.followup.send("ありがとうございます。\n担当者が対応いたします。しばらくお待ちください。")

        # 利用数を記録
        count = self.config.get_value(interaction.guild_id, "support", "used_count", default_value=0)
        count += 1
        self.config.set_value(interaction.guild_id, "support", "used_count", value=count)

        # 運営用に通知
        operate_ch = self.config.get_value(interaction.guild_id, "support", "operate_ch")
        if not operate_ch:
            return
        
        # 完了ボタン
        completion_button = discord.ui.Button(label="完了", style=discord.ButtonStyle.success, custom_id="support_completion")
        view = discord.ui.View()
        view.add_item(completion_button)

        notice_ch = interaction.guild.get_channel(operate_ch)
        await notice_ch.send(f"## 新しい購入手続きがあります\n{interaction.channel.jump_url}\nid:`{interaction.channel.id}`", view=view)

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