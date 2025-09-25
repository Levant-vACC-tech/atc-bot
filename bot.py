import discord
import asyncio
import requests
import os
from datetime import datetime

VATSIM_DATA_URL = "https://data.vatsim.net/v3/vatsim-data.json"
CHANNEL_ID = 1420399607661465673  # Replace with your channel ID

WATCHED_POSITIONS = ["ORBI_TWR", "ORBI_GND", "ORBI_DEL", "ORBI_APP", "ORBI_DEP", "ORBB_N_CTR", "ORBB_CTR", "ORBB_1_CTR", "ORBB_2_CTR", "ORBB_S_CTR", "ORBB_U_CTR", "ORBB_V_CTR", "ORNI_GND", "ORNI_TWR", "ORMM_GND", "ORMM_TWR", "OREZ_TWR", "ORER_TWR", "ORKK_GND", "ORKK_TWR", "ORBM_TWR", "ORAA_TWR", "OSDI_DEL", "OSDI_GND", "OSDI_TWR", "OSDI_APP", "OSDI_DEP", "OSDI_CTR", "OSAP_GND", "OSAP_TWR", "OSAP_APP", "OLBA_DEL", "OLBA_GND", "OLBA_APP", "OLBA_CTR", "ORBI_FMP", "OLBA_FMP", "OLBA_TWR", "ORSU_TWR"]

intents = discord.Intents.default()

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
                    current_atc = {c['callsign']: c for c in data.get("controllers", []) if c['callsign'] in WATCHED_POSITIONS}

                    # Check for new online ATC
                    for callsign, info in current_atc.items():
                        if callsign not in self.previous_atc:
                            pilot_name = info.get("name", "Unknown")
                            freq = info.get("frequency", "N/A")
                            file = discord.File("logo.png", filename="logo.png")
                            timestamp = datetime.utcnow().strftime("%H:%Mz")
                            file = discord.File("thumbnail.png", filename="thumbnail.png")

                            embed = discord.Embed(
                                title=f"{callsign} is Online",
                                color=0x00ff00  # green
                            )
                            embed.add_field(name="Callsign", value=callsign, inline=True)
                            embed.add_field(name="Frequency", value=freq, inline=True)
                            embed.add_field(name="Controller", value=f"{pilot_name} is online at {timestamp}", inline=False)
                            embed.set_thumbnail(url="attachment://thumbnail.png")
                            embed.set_footer(text="Levant vACC Operations")

                            await channel.send(file=file, embed=embed)

                    # Check for ATC that went offline
                    for callsign in list(self.previous_atc.keys()):
                        if callsign not in current_atc:
                            info = self.previous_atc[callsign]
                            pilot_name = info.get("name", "Unknown")
                            online_time = info.get("timestamp")
                            end_time = datetime.utcnow()
                            duration = end_time - online_time
                            file = discord.File("thumbnail.png", filename="thumbnail.png")

                            embed = discord.Embed(
                                title=f"{callsign} Disconnected",
                                color=0xff0000  # red
                            )
                            embed.add_field(name="Controller", value=f"{pilot_name} is now offline", inline=False)
                            embed.add_field(name="End Time", value=end_time.strftime("%H:%Mz"), inline=True)
                            embed.add_field(name="Session Duration", value=str(duration).split(".")[0], inline=True)
                            embed.set_thumbnail(url="attachment://thumbnail.png")
                            embed.set_footer(text="Levant vACC Operations")
                            await channel.send(file=file, embed=embed)

                    # Update previous_atc with timestamps
                    for callsign, info in current_atc.items():
                        info['timestamp'] = self.previous_atc.get(callsign, {}).get('timestamp', datetime.utcnow())
                    self.previous_atc = current_atc

            except Exception as e:
                print(f"Error: {e}")

            await asyncio.sleep(60)


client = MyClient(intents=intents)
token = os.environ.get("DISCORD_TOKEN")
client.run(token)




