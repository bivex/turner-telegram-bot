import asyncio
import config
from aiogram import Bot

async def main():
    bot = Bot(token=config.BOT_TOKEN)
    try:
        me = await bot.get_me()
        print(f"Bot Username: @{me.username}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
