from src.common.common import *


class Utility(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(
        name="upload",
        description="Upload an emoji.",
        usage=">upload [emoji name] [url]",
        aliases=["steal"],
    )
    @has_permissions(manage_emojis=True)
    async def upload(self, ctx, name, url: str = None, *, extra_args=""):
        """
        Upload an emoji from an image. There are a few options for how to do this:

            - Supply both a name and URL. They will both be used to upload the emoji directly.
            - Supply a name and an attachment image (as a file). The URL will be grabbed from the image.
            - Supply an emoji to be "stolen" in replacement of the name argument - the name and URL will be grabbed
            from this emoji.

        Any other formats are invalid and will cause an error.

        :param ctx:
        :param name: The name for the emoji.
        :param url: [Optional] The URL for the emoji's image.
        :param extra_args: [Optional] If this is present, the command is too long and should error.
        """
        # TODO: See if this code can be simplified
        # Too many arguments -- likely user tried a name like "my cool emoji" instead of "my_cool_emoji"
        if extra_args:
            raise Exception(
                "That doesn't look quite right. Make sure the emoji name is only one word."
            )

        # Both arguments are already provided :)
        if name and url:
            await upload_emoji(ctx, name, url)

        # Name specified, but no URL
        elif name and not url:

            # An attachment was uploaded, use that for the emoji URL
            if ctx.message.attachments:
                url = ctx.message.attachments[0].url
                await upload_emoji(ctx, name, url)

            # No attachments
            else:
                # Check if name is an emoji to be "stolen"
                emoji = await check_if_emoji(ctx, name)

                if emoji:
                    await upload_emoji(ctx, emoji.name, emoji.url)
                else:
                    raise Exception(
                        "That doesn't look quite right. Check `>help upload`."
                    )


def setup(bot):
    bot.add_cog(Utility(bot))
