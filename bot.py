import discord
import asyncio
import requests
import os
from datetime import datetime, timezone
from flask import Flask
import threading

# -----------------------------
# Config
# -----------------------------
VATSIM_DATA_URL = "https://data.vatsim.net/v3/vatsim-data.json"
CHANNEL_ID = 1421144864267173938  # Replace with your channel ID
WATCHED_POSITIONS = [
    "ORBI_TWR", "ORBI_GND", "ORBI_DEL", "ORBI_APP", "ORBI_DEP",
    "ORBB_N_CTR", "ORBB_CTR", "ORBB_1_CTR", "ORBB_2_CTR", "ORBB_S_CTR",
    "ORBB_U_CTR", "ORBB_V_CTR", "ORNI_GND", "ORNI_TWR", "ORMM_GND", "ORMM_TWR",
    "OREZ_TWR", "ORER_TWR", "ORKK_GND", "ORKK_TWR", "ORBM_TWR", "ORAA_TWR",
    "OSDI_DEL", "OSDI_GND", "OSDI_TWR", "OSDI_APP", "OSDI_DEP", "OSDI_CTR",
    "OSAP_GND", "OSAP_TWR", "OSAP_APP", "OLBA_DEL", "OLBA_GND", "OLBA_APP",
    "OLBA_CTR", "ORBI_FMP", "OLBA_FMP", "OLBA_TWR", "ORSU_TWR"
]

intents = discord.Intents.default()

# -----------------------------
# Discord Bot
# -----------------------------
class MyClient(discord.Client):
    def __init__(self, *, intents):
        super().__init__(intents=intents)
        self.previous_atc = {}

    async def setup_hook(self):
        self.bg_task = asyncio.create_task(self.check_vatsim())

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")

    async def check_vatsim(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Could not find channel. Check CHANNEL_ID.")
            return

        while not self.is_closed():
            try:
                r = requests.get(VATSIM_DATA_URL)
                if r.status_code == 200:
                    data = r.json()
                    current_atc = {
                        c['callsign']: c
                        for c in data.get("controllers", [])
                        if c['callsign'] in WATCHED_POSITIONS
                    }

                    current_callsigns = set(current_atc.keys())
                    previous_callsigns = set(self.previous_atc.keys())

                    # -----------------------------
                    # New online ATC
                    # -----------------------------
                    for callsign in current_callsigns - previous_callsigns:
                        info = current_atc[callsign]
                        pilot_name = info.get("name", "Unknown")
                        freq = info.get("frequency", "N/A")
                        timestamp = datetime.utcnow().strftime("%H:%M:%S UTC")

                        file = discord.File("thumbnail.png", filename="thumbnail.png")
                        embed = discord.Embed(
                            title=f"{callsign} is Online",
                            color=0x00ff00
                        )
                        embed.add_field(name="Callsign", value=callsign, inline=True)
                        embed.add_field(name="Frequency", value=freq, inline=True)
                        embed.add_field(
                            name="Controller",
                            value=f"{pilot_name} is online at {timestamp}",
                            inline=False
                        )
                        embed.set_thumbnail(url="attachment://thumbnail.png")
                        embed.set_footer(text="Levant vACC Operations")

                        await channel.send(file=file, embed=embed)

                    # -----------------------------
                    # ATC went offline
                    # -----------------------------
                    for callsign in previous_callsigns - current_callsigns:
                        info = self.previous_atc[callsign]
                        pilot_name = info.get("name", "Unknown")
                        timestamp = datetime.utcnow().strftime("%H:%M:%S UTC")
                        logon_time_str = info.get("logon_time")

                        # Session length
                        online_time = "Unknown"
                        if logon_time_str:
                            logon_time = datetime.fromisoformat(logon_time_str.replace("Z", "+00:00"))
                            duration = datetime.now(timezone.utc) - logon_time
                            total_seconds = int(duration.total_seconds())
                            hours, remainder = divmod(total_seconds, 3600)
                            minutes, seconds = divmod(remainder, 60)
                            online_time = f"{hours}h {minutes}m {seconds}s"

                        file = discord.File("thumbnail.png", filename="thumbnail.png")
                        embed = discord.Embed(
                            title=f"{callsign} Disconnected",
                            color=0xff0000
                        )
                        embed.add_field(
                            name="Controller",
                            value=f"{pilot_name} is now offline",
                            inline=False
                        )
                        embed.add_field(name="End Time", value=timestamp, inline=True)
                        embed.add_field(name="Session Duration", value=online_time, inline=True)
                        embed.set_thumbnail(url="attachment://thumbnail.png")
                        embed.set_footer(text="Levant vACC Operations")
                        await channel.send(file=file, embed=embed)

                    # -----------------------------
                    # Update previous_atc
                    # -----------------------------
                    self.previous_atc = {
                        callsign: current_atc[callsign]
                        for callsign in current_callsigns
                    }

            except Exception as e:
                print(f"Error: {e}")

            await asyncio.sleep(60)

# -----------------------------
# Flask Web Server (keeps Render alive)
# -----------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Levant vACC Bot is running!"

def run_discord_bot():
    token = os.environ.get("DISCORD_TOKEN")
    client = MyClient(intents=intents)
    client.run(token)

# Run Discord bot in a background thread
threading.Thread(target=run_discord_bot, daemon=True).start()

# -----------------------------
# Start Flask (main Render process)
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
