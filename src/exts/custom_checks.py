from src.common.common import *


class CustomChecks(Cog):
    __slots__ = ["bot"]

    def __init__(self, bot):
        self.bot = bot

    async def bot_check(self, ctx):
        """
        Checks that affect the entire bot.

        Checks implemented:
            - cooldown: A global cooldown for every command.

        """

        async def cooldown_check() -> bool:
            """ Implement a global cooldown for every command, defined in bot.cooldown. """
            whitelist = ("help",)

            if ctx.command.name in whitelist:
                return True

            # Get current cooldown
            bucket = self.bot.cooldown.get_bucket(ctx.message)
            retry_after = bucket.update_rate_limit()

            if retry_after:  # On cooldown
                await ctx.send_error(
                    "You're on cooldown. Try again in %d seconds." % int(retry_after)
                )
                return False
            else:  # Not on cooldown
                return True

        # Checks not in this tuple will be ignored
        active_checks = (cooldown_check,)

        # Loop through every check
        # Every check must return True for the command to continue
        # When adding new checks, use ctx.send_error and then return False on fail
        for c in active_checks:
            if not await c():
                return False

        return True


def setup(bot):
    bot.add_cog(CustomChecks(bot))
