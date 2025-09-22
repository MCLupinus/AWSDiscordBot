import os
import sys
if __name__ == "__main__":
    os.chdir(".")
    sys.path.append(os.getcwd())
    
    # main.pyを実行
    os.system(f"{sys.executable} main.py")
    
import discord
from Database import Database

PAYMENT_METHOD = [
    "クレジットカード"
]

class PremiseSelectMenu(discord.ui.View):
    def __init__(self, button_data:dict, format:str):
        super().__init__(timeout=None)
        self.button_data = button_data
        self.premise_selection = None
        self.payment_selection = PAYMENT_METHOD[0]
        self.format = format
        self.config = Database("config.json")

        self.add_item(self.premise_menu(button_data["select_menu"]))
        # 購入だったら購入方法を追加
        if format == "purchase":
            self.add_item(self.payment_menu())
        self.add_item(self.decision_button())

    def premise_menu(self, select_menu: list[str]) -> discord.ui.Select:
        options = []
        is_first = True
        for i in range(len(select_menu)):
            options.append(discord.SelectOption(label=select_menu[i], default=is_first))
            if is_first:
                self.premise_selection = select_menu[0]
                is_first = False

        select = discord.ui.Select(placeholder="カテゴリを選択してください", options=options)
        select.callback = self.premise_select_callback
        return select
    
    def payment_menu(self) -> discord.ui.Select:
        options = []
        is_first = True
        for i in range(len(PAYMENT_METHOD)):
            options.append(discord.SelectOption(label=PAYMENT_METHOD[i], default=is_first))
            if is_first:
                is_first = False

        select = discord.ui.Select(placeholder="カテゴリを選択してください", options=options)
        select.callback = self.payment_select_callback
        return select
    
    def decision_button(self) -> discord.ui.Button:
        button = discord.ui.Button(label="決定", style=discord.ButtonStyle.success)
        button.callback = self.quantity_button_callback
        return button
    
    async def premise_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.premise_selection = interaction.data["values"][0].title()

    async def payment_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.payment_selection = interaction.data["values"][0].title()

    async def quantity_button_callback(self, interaction: discord.Interaction):
        if self.format == "forum":
            # 入力フォーラムを表示
            await interaction.response.send_modal(SupportForum(self.button_data, self.premise_selection, interaction))
        elif self.format == "purchase":
            # プライベートチャンネルを開く
            # セレクトメニューメッセージを削除
            await interaction.delete_original_response()
            title = str(self.premise_selection)

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
            await thread.send(f"支援ありがとうございます。選択された内容は以下のとおりでお間違いありませんか？\n購入内容: **{self.premise_selection}**\nお支払い方法: **{self.payment_selection}**\n\n「はい」を押すまで手続きは進行しません。\n内容の変更はお支払いが完了するまでいつでも可能です。", view=view)

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
        await thread.send(self.detail)
        
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
        await notice_ch.send(f"## 新しいお問い合わせがあります\n質問者: {interaction.user.mention}\n[{title}]({thread.jump_url})\nid:`{thread.id}`", view=view)
