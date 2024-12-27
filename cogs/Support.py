import os
import sys
if __name__ == "__main__":
    os.chdir(".")
    sys.path.append(os.getcwd())
    
    # main.pyを実行
    os.system(f"{sys.executable} main.py")
    
import discord
from discord import app_commands
from discord.ext import commands
from Database import Database

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if isinstance(channel, discord.TextChannel) and "ticket" in channel.name.lower():
            print(f"[サポート] {channel.name}チャンネルが作成されました")
            container = Database("config.json")
            data = container.load_or_create_json()

            # ギルドIDを取得して文字列化
            guild_id = str(channel.guild.id)

            # ギルドIDが見つかったのでデータを取得
            try:
                priority_role = data[guild_id]['priority_response']['roles']        # ロール
                priority_category = data[guild_id]['priority_response']['category'] # カテゴリー
            except:    
                print("[サポート] error: 優先対応するロールとカテゴリーを設定してください")
                return

            # チャンネルのメンバーをフェッチ
            channel_members = []
            async for member in channel.guild.fetch_members(limit=None):
                if channel.permissions_for(member).read_messages:
                    channel_members.append(member)

            # 特定のロールを持つメンバーがいるか確認
            for member in channel_members:
                for role in member.roles:
                    if role.id in priority_role:
                        # チャンネルを「優先対応」カテゴリに移動
                        target_category = channel.guild.get_channel(priority_category)
                        try:
                            await channel.edit(category=target_category, position=0)
                            print(f"[サポート] {channel.name} を優先対応カテゴリに移動しました。")
                        except:
                            print(f"[サポート] {channel.name} はカテゴリが超過しているため移動できませんでした。")
                        await channel.send(f"```📌このお問い合わせは優先対応としてマークされました。```\n{discord.utils.get(channel.guild.roles, name="運営").mention}の対応を暫くお待ち下さい")
                        return
            
            print("[サポート] 優先対応が必要なメンバーはいません。")
                        
    @app_commands.command(name="priority", description="対象の問い合わせを優先対応として扱います")
    @app_commands.checks.has_any_role("運営", "Discord対応")
    async def force_priority(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        # チャンネルが指定されていない場合、現在のチャンネルを使用
        channel = channel or interaction.channel
        
        container = Database("config.json")
        data = container.load_or_create_json()

        # ギルドIDが見つからなければここで終了
        if not str(channel.guild.id) in data:
            await channel.send("このサーバーのデータが見つかりませんでした\n`/reload`を試してください", ephemeral=True)
            return

        guild_id = str(channel.guild.id)

        # ギルドIDが見つかったのでデータを取得
        priority_category = data[guild_id]['priority_response']['category'] # カテゴリー
        
        if not priority_category:
            await interaction.response.send_message(f"エラー: カテゴリが見つかりませんでした")
            return

        try:
            # チャンネルを優先対応カテゴリに移動
            priority_category_obj = interaction.guild.get_channel(int(priority_category))

            if priority_category_obj and isinstance(priority_category_obj, discord.CategoryChannel):
                await channel.edit(category=priority_category_obj, position=len(priority_category_obj.channels))
                await interaction.response.send_message(f"{channel.mention} を優先対応カテゴリに移動しました。")
                await channel.send(f"```📌このお問い合わせは優先対応としてマークされました。```\n{discord.utils.get(channel.guild.roles, name="運営").mention}の対応を暫くお待ち下さい")
            else:
                await interaction.response.send_message(f"```📌このお問い合わせは優先対応としてマークされました。```\n{discord.utils.get(channel.guild.roles, name="運営").mention}の対応を暫くお待ち下さい")
        except discord.Forbidden:
            await interaction.response.send_message("チャンネルを移動する権限がありません。")
        except discord.HTTPException:
            await interaction.response.send_message("チャンネルの移動中にエラーが発生しました。")

async def setup(bot):
    await bot.add_cog(Support(bot))