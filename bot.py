import discord
import asyncio
import requests
import os
from datetime import datetime
from flask import Flask
import threading

# -----------------------------
# Config
# -----------------------------
VATSIM_DATA_URL = "https://data.vatsim.net/v3/vatsim-data.json"
CHANNEL_ID = 1420399607661465673  # Replace with your channel ID
WATCHED_POSITIONS = ["ORBI_TWR", "ORBI_GND", "ORBI_DEL", "ORBI_APP", "ORBI_DEP", "ORBB_N_CTR", "ORBB_CTR", "ORBB_1_CTR", "ORBB_2_CTR", "ORBB_S_CTR", "ORBB_U_CTR", "ORBB_V_CTR", "ORNI_GND", "ORNI_TWR", "ORMM_GND", "ORMM_TWR", "OREZ_TWR", "ORER_TWR", "ORKK_GND", "ORKK_TWR", "ORBM_TWR", "ORAA_TWR", "OSDI_DEL", "OSDI_GND", "OSDI_TWR", "OSDI_APP", "OSDI_DEP", "OSDI_CTR", "OSAP_GND", "OSAP_TWR", "OSAP_APP", "OLBA_DEL", "OLBA_GND", "OLBA_APP", "OLBA_CTR", "ORBI_FMP", "OLBA_FMP", "OLBA_TWR", "ORSU_TWR"]

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
                        file = discord.File("thumbnail.png", filename="thumbnail.png")
                        timestamp = datetime.utcnow().strftime("%H:%M UTC")

                        embed = discord.Embed(
                            title=f"{callsign} is Online",
                            color=0x00ff00
                        )
                        embed.add_field(name="Callsign", value=callsign, inline=True)
                        embed.add_field(name="Frequency", value=freq, inline=True)
                        embed.add_field(name="Controller",
