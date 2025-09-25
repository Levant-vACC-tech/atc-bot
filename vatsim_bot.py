import discord
import requests
import asyncio

TOKEN = "MTQyMDQwMDc5MDAzMTU2ODg5Nw.GX_HQR.uNxxlU8ppYGqEhTd4-oqcqlrxtdy7-sGKZQjd4"
CHANNEL_ID = 1420399607661465673  # Replace with your channel ID
CHECK_INTERVAL = 60
WATCHED_POSITIONS = ["OLBA_APP", "OJAI_TWR", "LCLK_CTR"]

intents = discord.Intents.default()
client = discord.Client(intents=intents)

last_seen = set()

async def check_vatsim():
    global last_seen
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while True:
        try:
            r = requests.get("https://data.vatsim.net/v3/vatsim-data.json")
            data = r.json()
            online_positions = {c['callsign'] for c in data['controllers'] if c['callsign'] in WATCHED_POSITIONS}
            new_positions = online_positions - last_seen

            for pos in new_positions:
                await channel.send(f"🟢 {pos} is now online on VATSIM!")

            last_seen = online_positions
        except Exception as e:
            print(f"Error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    await client.login(TOKEN)
    # schedule the vatsim check task properly
    asyncio.create_task(check_vatsim())
    await client.connect()

# Run the bot
asyncio.run(main())
