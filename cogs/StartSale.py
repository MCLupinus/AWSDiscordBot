import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
import asyncio
import pytz
import json
import os

SALE_CHANNEL = "💎有料プラン-セール中"
DEFAULT_CHANNEL = "💎有料プラン"
SAVE_FILE = "bot_data.json"
DEFAULT_DURATION = 72

class Sale(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sale_time = self.load_sale_time()
        self.check_permissions.start()

    def cog_unload(self):
        self.check_permissions.cancel()

    def load_sale_time(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                return {int(k): {int(uk): datetime.datetime.fromisoformat(uv) for uk, uv in v.items()} for k, v in data.items() if k != 'default_duration'}
        return {}

    def load_default_duration(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('default_duration', DEFAULT_DURATION)
        return DEFAULT_DURATION

    def save_sale_time(self):
        data = {}
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)

        sale_time_data = {str(k): {str(uk): uv.isoformat() for uk, uv in v.items()} for k, v in self.sale_time.items()}
        data.update(sale_time_data)

        if 'default_duration' not in data:
            data['default_duration'] = self.load_default_duration()

        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)

    @app_commands.command(name="sale_start", description="指定時間チャンネルの権限を変更します")
    @app_commands.describe(
        target="権限を変更する対象（ユーザーまたはロール）",
        duration="権限を変更する時間（時間単位、0.5-720）デフォルト: 72時間"
    )
    @commands.has_any_role('管理者', 'Discord対応')
    async def start_sale(self, interaction: discord.Interaction, target: discord.Member | discord.Role, duration: float = None):
        await interaction.response.defer(ephemeral=True)

        try:
            if duration is None:
                duration = self.load_default_duration()
            
            if duration < 0.5 or duration > 720:
                await interaction.followup.send("時間は0.5時間（約30分）から720時間（30日）の間で指定してください。", ephemeral=True)
                return

            channel1 = discord.utils.get(interaction.guild.channels, name=SALE_CHANNEL)
            channel2 = discord.utils.get(interaction.guild.channels, name=DEFAULT_CHANNEL)

            if not channel1 or not channel2:
                await interaction.followup.send("指定されたチャンネルが見つかりません。", ephemeral=True)
                return

            affected_members = []

            if isinstance(target, discord.Member):
                await self.apply_sale_to_member(target, duration, channel1, channel2)
                affected_members.append(target)
            elif isinstance(target, discord.Role):
                for member in interaction.guild.members:
                    if target in member.roles:
                        await self.apply_sale_to_member(member, duration, channel1, channel2)
                        affected_members.append(member)

            duration_str = self.format_duration(duration)
            print(f"{target.name}に{duration_str}の間権限を変更しました。")
            
            await interaction.followup.send(
                f"{target.mention}" + (f"のメンバー{len(affected_members)}人" if isinstance(target, discord.Role) else "") +
                f"の権限を{duration_str}変更しました。", 
                ephemeral=True
            )
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            await interaction.followup.send("コマンドの実行中にエラーが発生しました。", ephemeral=True)

    async def apply_sale_to_member(self, member: discord.Member, duration: float, channel1: discord.TextChannel, channel2: discord.TextChannel):
        await channel1.set_permissions(member, read_messages=True, send_messages=False)
        await channel2.set_permissions(member, read_messages=False, send_messages=False)

        expiration_time = datetime.datetime.now(pytz.UTC) + datetime.timedelta(hours=duration)
        
        if member.guild.id not in self.sale_time:
            self.sale_time[member.guild.id] = {}

        self.sale_time[member.guild.id][member.id] = expiration_time
        self.save_sale_time()

        duration_str = self.format_duration(duration)
        print(f"{member.name}に{duration_str}のセール期間を設定しました。期限: {expiration_time}")

    @app_commands.command(name="sale_start_from_join", description="参加日に基づいてセールを設定します")
    @app_commands.describe(target="セールを適用するユーザーまたはロール")
    @commands.has_any_role('管理者', 'Discord対応')
    async def start_sale_from_join(self, interaction: discord.Interaction, target: discord.Member | discord.Role):
        await interaction.response.defer(ephemeral=True)

        try:
            affected_members = []

            if isinstance(target, discord.Member):
                await self.apply_sale_from_join(target, interaction.guild)
                affected_members.append(target)
            elif isinstance(target, discord.Role):
                for member in interaction.guild.members:
                    if target in member.roles:
                        await self.apply_sale_from_join(member, interaction.guild)
                        affected_members.append(member)

            await interaction.followup.send(
                f"{target.mention}" + (f"のメンバー{len(affected_members)}人" if isinstance(target, discord.Role) else "") +
                f"に対して、参加日に基づいてセールを適用しました。", 
                ephemeral=True
            )
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            await interaction.followup.send("コマンドの実行中にエラーが発生しました。", ephemeral=True)

    async def apply_sale_from_join(self, member: discord.Member, guild: discord.Guild):
        join_date = member.joined_at
        if join_date.tzinfo is None:
            join_date = pytz.UTC.localize(join_date)
        
        current_time = datetime.datetime.now(pytz.UTC)
        days_since_join = (current_time - join_date).days
        
        if days_since_join < 4:
            sale_end_date = join_date + datetime.timedelta(days=3)
            duration = (sale_end_date - current_time).total_seconds() / 3600  # 時間単位に変換
        else:
            duration = 24  # 1日間 (24時間)

        channel1 = discord.utils.get(guild.channels, name=SALE_CHANNEL)
        channel2 = discord.utils.get(guild.channels, name=DEFAULT_CHANNEL)

        if channel1 and channel2:
            await self.apply_sale_to_member(member, duration, channel1, channel2)
            print(f"{member.name}に{self.format_duration(duration)}のセールを適用しました。（参加後{days_since_join}日）")
        else:
            print(f"必要なチャンネルが見つかりません。セールを適用できませんでした。")

    def format_duration(self, duration: float) -> str:
        if duration >= 24:
            days = int(duration // 24)
            hours = duration % 24
            return f"{days}日と{hours:.2f}時間"
        elif duration >= 1:
            return f"{duration:.2f}時間"
        else:
            minutes = int(duration * 60)
            return f"{minutes}分"
        
    @tasks.loop(minutes=5)
    async def check_permissions(self):
        await self.permission_check()

    @check_permissions.before_loop
    async def before_check_permissions(self):
        await self.bot.wait_until_ready()
        await self.permission_check()

    async def permission_check(self):
        now = datetime.datetime.now(pytz.UTC)
        changed = False

        print(f"権限チェックを実行：{now}")

        for guild in self.bot.guilds:
            if guild.id not in self.sale_time:
                continue

            print(f"ギルド {guild.name} をチェック中")
            channel1 = discord.utils.get(guild.channels, name=SALE_CHANNEL)
            channel2 = discord.utils.get(guild.channels, name=DEFAULT_CHANNEL)

            if not channel1 or not channel2:
                print(f"ギルド {guild.name} に必要なチャンネルが見つかりません")
                continue

            users_to_reset = []
            for user_id, expiration_time in list(self.sale_time[guild.id].items()):
                if expiration_time.tzinfo is None:
                    expiration_time = pytz.UTC.localize(expiration_time)
                
                time_diff = now - expiration_time
                print(f"ユーザー {user_id} をチェック中. 期限: {expiration_time}, 現在時刻: {now}, 差分: {time_diff}")
                
                if time_diff.total_seconds() >= 0:
                    users_to_reset.append(user_id)
                    print(f"期限切れ: ユーザー {user_id}, 現在時刻: {now}, 期限: {expiration_time}")
                else:
                    print(f"ユーザー {user_id} の権限はまだ有効です。残り時間: {-time_diff}")

            if users_to_reset:
                changed = True
                for user_id in users_to_reset:
                    member = guild.get_member(user_id)
                    if member:
                        await self.reset_member_permissions(member, channel1, channel2)
                    else:
                        print(f"ユーザー {user_id} がギルド {guild.name} に見つかりません。データから削除します。")
                    del self.sale_time[guild.id][user_id]

                print(f"{guild.name}の{len(users_to_reset)}人のユーザーの権限をリセットしました。")

        if changed:
            self.save_sale_time()
        else:
            print("変更はありませんでした。")

    async def reset_member_permissions(self, member: discord.Member, channel1: discord.TextChannel, channel2: discord.TextChannel):
        # チャンネル1の権限を削除
        await channel1.set_permissions(member, overwrite=None)
        
        # チャンネル2に追加（権限を付与）
        await channel2.set_permissions(member, read_messages=True, send_messages=False)
        
        # チャンネル2のメンバーリストに追加
        if isinstance(channel2, discord.TextChannel):
            try:
                await channel2.edit(overwrites={
                    **channel2.overwrites,
                    member: discord.PermissionOverwrite(read_messages=True, send_messages=False)
                })
            except discord.errors.Forbidden:
                print(f"チャンネル2 ({channel2.name}) にメンバー {member.name} を追加する権限がありません。")

async def setup(bot):
    await bot.add_cog(Sale(bot))