# Emojis
Emojis is an emoji management Discord bot. You can **[invite it to your server](https://discord.com/oauth2/authorize?client_id=749301838859337799&permissions=1946545248&scope=bot)**, or try it out in the **[support server](https://discord.gg/wzG9Y8s)**.

## Getting started
### Emoji replacement (fake Nitro)
Emojis can replace unparsed `:emojis:` that you post in the chat, so that you can use Nitro emojis for free. 

To use this, just type out the emoji as you normally would (like `:emoji_name:`). If Emojis finds an emoji with the same name, it'll replace it, like this:

![Example <](https://i.imgur.com/jFu5ECQ.png "Example")

### Uploading emojis
The command for uploading emojis is `>upload`. There are a few ways of using it:
- Supply both a name and URL. They will both be used to upload the emoji directly.
    - **Example:** `>upload my_emoji https://i.imgur.com/jFu5ECQ.png`
- Supply a name and an attachment image (as a file). The URL will be grabbed from the image.
    - **Example:** Attach a file, then, in the comment section, type `>upload my_emoji`.
- **This one needs Discord Nitro:** Supply an emoji to be "stolen" in replacement of the name argument - the name and URL will be grabbed from this emoji.
    - **Example:** `>upload :nitro_emoji:`
    
## Contributing
We'd love for you to contribute! Join the Discord (linked above) and let us know about your ideas for the bot. If you know Python, feel free to make a pull request and implement it yourself :)