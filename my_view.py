import discord

class My_View(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=180)
        self.user=user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        check = (interaction.user.id == self.user.id)
        if not check:
            await interaction.response.send_message(
                'Only the original command user can change this',
                ephemeral=True
            )
        return check

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
