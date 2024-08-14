import discord
from discord import app_commands
from discord.ext import commands

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.priority_role_names = ["DIAMONDメンバー", "PLATINUMメンバー"]  # 特定のロールの名前を指定
        self.priority_category_name = "優先対応"  # 「優先対応」カテゴリの名前を指定

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if isinstance(channel, discord.TextChannel) and "ticket" in channel.name.lower():
            print(f"新しいチケットチャンネルが作成されました: {channel.name}")
            
            # 優先ロールを名前で取得
            for priority_role_name in self.priority_role_names:
                priority_role = discord.utils.get(channel.guild.roles, name=priority_role_name)
                if priority_role:
                    break

            if not priority_role:
                print(f"エラー: '{priority_role_name}' ロールが見つかりません。")
                return

            # チャンネルのメンバーをフェッチ
            channel_members = []
            async for member in channel.guild.fetch_members(limit=None):
                if channel.permissions_for(member).read_messages:
                    channel_members.append(member)
            
            # 特定のロールを持つメンバーがいるか確認
            has_priority_member = any(priority_role in member.roles for member in channel_members)
            
            if has_priority_member:
                # 「優先対応」カテゴリを名前で取得
                priority_category = discord.utils.get(channel.guild.categories, name=self.priority_category_name)
                
                if priority_category:
                    # チャンネルを「優先対応」カテゴリに移動
                    await channel.edit(category=priority_category, position=0)
                    print(f"{channel.name} を優先対応カテゴリに移動しました。")
                    await channel.send("```📌このお問い合わせは優先対応としてマークされました。```")
                else:
                    print(f"エラー: '{self.priority_category_name}' カテゴリが見つかりません。")
            else:
                print("優先対応が必要なメンバーはいません。")

    @app_commands.command(name="priority", description="対象の問い合わせを優先対応として扱います")
    @app_commands.checks.has_any_role("運営", "Discord対応")
    async def force_priority(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        # チャンネルが指定されていない場合、現在のチャンネルを使用
        channel = channel or interaction.channel

        # チャンネル名に "ticket" が含まれているか確認
        if "ticket" not in channel.name.lower():
            await interaction.response.send_message("このコマンドは 'ticket' を含むチャンネル名に対してのみ使用できます。")
            return

        # 優先対応カテゴリを取得
        priority_category = discord.utils.get(interaction.guild.categories, name=self.priority_category_name)
        
        if not priority_category:
            await interaction.response.send_message(f"エラー: '{self.priority_category_name}' カテゴリが見つかりません。")
            return

        try:
            # チャンネルを優先対応カテゴリに移動
            await channel.edit(category=priority_category, position=len(priority_category.channels))
            if channel != interaction.channel:
                await interaction.response.send_message(f"{channel.mention} を優先対応カテゴリに移動しました。")
                await channel.send("```📌このお問い合わせは優先対応としてマークされました。```")
            else:
                await interaction.response.send_message("```📌このお問い合わせは優先対応としてマークされました。```")
        except discord.Forbidden:
            await interaction.response.send_message("チャンネルを移動する権限がありません。")
        except discord.HTTPException:
            await interaction.response.send_message("チャンネルの移動中にエラーが発生しました。")

async def setup(bot):
    await bot.add_cog(Support(bot))