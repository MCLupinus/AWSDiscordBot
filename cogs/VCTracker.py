import os
import sys
if __name__ == "__main__":
    os.chdir(".")
    sys.path.append(os.getcwd())
    
    # main.pyを実行
    os.system(f"{sys.executable} main.py")

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.utils import get
from Database import Database
from datetime import datetime, timedelta

TRACKER_INDEX = "VCtrackingTime"

class VCTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Database("config.json")
        self.context = Database("context.json")
        self.check_schedule.start()

    # 有効無効切り替え
    @app_commands.command(name="vctracker_active", description="VCの有効状態を切り替えます")
    @commands.has_any_role('管理者', 'Discord対応')
    @app_commands.describe(is_active = "有効か無効かを切り替え")
    async def set_active(self, interaction: discord.Interaction, is_active: bool):
        self.config.set_value(str(interaction.guild_id), TRACKER_INDEX, "active", value=is_active)
        active_text = "有効" if is_active else "無効"
        await interaction.response.send_message(self.context.get_value("message", "vc_monitoring") % active_text)

    # 設定
    @app_commands.command(name="vctracker_set", description="VCの開放時間と終了までの時間を設定します")
    @commands.has_any_role('管理者', 'Discord対応')
    @app_commands.describe(
        open_hours="開始する時間を設定します",
        open_minutes="開始する分を設定します",
        open_period="解放している時間を設定します(分)",
        category="ボイスチャンネルを作成するカテゴリを設定します"
    )
    async def set(self, interaction: discord.Interaction, open_hours: int, open_minutes: int, open_period: int, category: str = None):
        # エラー処理
        is_valid_hours = 0 <= open_hours <= 23
        is_valid_minutes = 0 <= open_minutes <= 59
        if not is_valid_hours or not is_valid_minutes:
            await interaction.response.send_message(self.context.get_value("message", "value_error") % ("時間", "0時0分から23時59分"), ephemeral=True)
            return

        # 開放時間が範囲外であれば終了
        if not (0 <= open_period < 1440):
            await interaction.response.send_message(self.context.get_value("message", "value_error") % ("開放時間", "0分から1439分"), ephemeral=True)
            return

        # 時間かかるかもしれないから一旦返事
        await interaction.response.defer()
        result_message = "```diff\n"

        # カテゴリを設定
        if category == None:
            try:
                category_id = self.config.get_value(str(interaction.guild_id), TRACKER_INDEX, "category")
            except:
                category_id = None
        else:
            try:
                category_id = int(category)
            except:
                category_id = None

        if get(interaction.guild.categories, id=category_id):
            result = category_id
            result_message += self.context.get_value("message", "create_category") % {interaction.guild.get_channel(category_id).name}
        else:
            result = None
            result_message += "- " + self.context.get_value("message", "id_not_found")
        
        self.config.set_value(str(interaction.guild_id), TRACKER_INDEX, "category", value=result)

        # 時間を初期化
        base_date = datetime(1, 1, 1)

        try:
            open_time = base_date.replace(hour=open_hours, minute=open_minutes)
            close_time = open_time + timedelta(minutes=open_period)

            # 終了時間が開始時間より前であれば次の日を終了時間に設定
            if close_time < open_time:
                end_time += timedelta(days=1)

            self.config.set_value(str(interaction.guild_id), TRACKER_INDEX, "open", value=open_time.strftime('%Y-%m-%d %H:%M:%S'))
            self.config.set_value(str(interaction.guild_id), TRACKER_INDEX, "close", value=close_time.strftime('%Y-%m-%d %H:%M:%S'))
            result_message += self.context.get_value("message", "vc_setting_result") % (f"{open_hours:02d}", f"{open_minutes:02d}", open_period)
        except ValueError as e:
            result_message += "- " + self.context.get_value("message", "fraud_date")

        result_message += "```"
        await interaction.followup.send(result_message)

    @tasks.loop(minutes=1)
    async def check_schedule(self):
        # 時間が取得できたギルドだけに実行する
        try:
            data = self.config.load_or_create_json()
            guild_ids = list(data.keys())
        except:
            self.bot.logger.error(self.context.get_value("system_log", "server_not_found"))
            return

        now = datetime.now()
        for guild_id in guild_ids:
            # 開始と終了を取得
            try:
                if not self.config.get_value(str(guild_id), TRACKER_INDEX, "active", default_value=True):
                    # 無効化されていたら終了
                    self.bot.logger.info(self.context.get_value("system_log", "disabled"))
                    return
                open_time_data = self.config.get_value(guild_id, TRACKER_INDEX, "open")
                open_time: datetime = datetime.strptime(self.date_Normalize(open_time_data), '%Y-%m-%d %H:%M:%S')
                close_time_data = self.config.get_value(guild_id, TRACKER_INDEX, "close")
                close_time: datetime = datetime.strptime(self.date_Normalize(close_time_data), '%Y-%m-%d %H:%M:%S')
            except:
                self.bot.logger.error(self.context.get_value("system_log", "not_released") % (self.bot.get_guild(guild_id).name))
                return

            # 対象時間を正規化
            ## 開始は現在日付に合わせる
            open_time = open_time.replace(year=now.year, month=now.month, day=now.day)
            ## 終了は現在日付に日付を跨いだ場合のことを考慮する
            close_date = now + timedelta(days=close_time.day - 1)
            close_time = close_date.replace(hour=close_time.hour, minute=close_time.minute, second=close_time.second)

            try:
                # 既に存在すれば取得
                vc_group:list[int] = self.config.get_value(guild_id, TRACKER_INDEX, "managed_vc")
            except:
                # 存在しなければ作成
                vc_group = []

            # 現在時刻と開放時刻を比較
            if open_time <= now < close_time:
                # 開放時間内の処理
                if len(vc_group) == 0:
                    # チャンネルが存在しなければ作成する
                    vc = await self.create_voice_ch(guild_id)
                    self.bot.logger.info(self.context.get_value("system_log", "server_add_vc") % (guild_id, vc.name))
                else:
                    # 開開放VCが多すぎないかチェックする
                    guild: discord.Guild = self.bot.get_guild(int(guild_id))
                    keep = True
                    print("使われていないVCが存在します")
                    for vc in vc_group:
                        voice_ch = get(guild.channels, id = vc)

                        if len(voice_ch.members) == 0 and not keep:
                            await self.remove_voice_ch(guild_id, vc)

                        if len(voice_ch.members) == 0:
                            print("削除対象を発見")
                            keep = False

            elif not (open_time <= now < close_time):
                # 開放時間外の処理
                if len(vc_group) == 0:
                    self.bot.logger.info(self.context.get_value("system_log", "closing_time"))
                    return
                # 開放中のVCを削除
                for removalbe_vc in vc_group:
                    await self.remove_voice_ch(guild_id, removalbe_vc)

                self.bot.logger.info(self.context.get_value("system_log", "server_vc_closed") % (guild_id))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        if self.bot.user.mentioned_in(message):
            self.check_schedule.restart()
            await message.channel.send(self.context.get_value("message", "update_monitoring_time"))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # VCに参加した場合
        if before.channel is None and after.channel is not None:
            vc_group:list[int] = self.config.get_value(member.guild.id, TRACKER_INDEX, "managed_vc", default_value=[])

            if len(vc_group) == 0:
                # 開かれているVCが無ければ終了
                return

            is_space = False
            for vc in vc_group:
                voice_ch = get(member.guild.voice_channels, id=vc)
                if len(voice_ch.members) == 0:
                    # 誰も入っていないチャンネルがあればフラグを立てる
                    is_space = True
                    break

            if not is_space:
                # 誰も入っていないチャンネルがなければ新規作成する
                await self.create_voice_ch(member.guild.id)

    async def create_voice_ch(self, guild_id) -> discord.VoiceChannel:
        guild: discord.Guild = self.bot.get_guild(int(guild_id))
        try:
            # データの取得を試みる
            category_id = self.config.get_value(guild_id, TRACKER_INDEX, "category")
            category = get(guild.categories, id=category_id)
        except:
            category = None
        try:
            # 既に存在すれば取得
            vc_group:list[int] = self.config.get_value(guild_id, TRACKER_INDEX, "managed_vc")
        except:
            # 存在しなければ作成
            vc_group = []

        if len(vc_group) >= 10:
            # 10個以上VCが作られていたらそれ以上を制限する
            return

        # VCを作成
        voice_ch = await guild.create_voice_channel(name=f"自由参加VC_{len(vc_group)}", category=category)
        vc_group.append(voice_ch.id)

        # グループを登録
        self.config.set_value(guild_id, TRACKER_INDEX, "managed_vc", value=vc_group)

        return voice_ch
    
    async def remove_voice_ch(self, guild_id, vc_id):
        try:
            # 既に存在すれば取得
            vc_group:list[int] = self.config.get_value(guild_id, TRACKER_INDEX, "managed_vc", default_value=[])
        except:
            # 存在しなければ終了
            return
        try:
            guild: discord.Guild = self.bot.get_guild(int(guild_id))
            voice_ch: discord.VoiceChannel = get(guild.channels, id=vc_id)

            await voice_ch.delete()
            self.bot.logger.info(self.context.get_value("system_log", "channel_removed") % vc_id)

            # リストからも削除
            vc_group.remove(vc_id)
            self.config.set_value(guild_id, TRACKER_INDEX, "managed_vc", value=vc_group)

        except:
            self.bot.logger.error(self.context.get_value("system_log", "deleting_channel_error"))

    def date_Normalize(self, date: str) -> str:
        if len(date.split('-')[0]) < 4:
            year, rest = date.split('-', 1)
            date = f"{int(year):04d}-{rest}"
        return date

    @check_schedule.before_loop
    async def before_check_schedule(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(VCTracker(bot))