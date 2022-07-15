from lavalink import add_event_hook
from lavalink.events import NodeConnectedEvent, NodeDisconnectedEvent
from nextcord import Interaction, slash_command
from nextcord.ext.commands import Cog
from typing import get_args, Optional
from utils.database import Database
from utils.jockey import Jockey
from utils.jockey_helpers import create_error_embed
from utils.lavalink import init_lavalink
from utils.lavalink_helpers import EventWithPlayer
from utils.lavalink_bot import LavalinkBot
from utils.spotify_client import Spotify


class PlayerCog(Cog):
    def __init__(self, bot: LavalinkBot, db: Database):
        self._bot = bot
        self._db = db
        
        # Spotify client
        self.spotify_client = Spotify()

        # Jockey instances
        self._jockeys = {}

        # Create Lavalink client instance
        if bot.lavalink == None:
            bot.lavalink = init_lavalink(bot.user.id)

        # Listen to Lavalink events
        add_event_hook(self.on_lavalink_event)

        print(f'Loaded cog: {self.__class__.__name__}')
    
    async def on_lavalink_event(self, event: EventWithPlayer):
        # Does the event have a player attribute?
        if isinstance(event, get_args(EventWithPlayer)):
            # Dispatch event to appropriate jockey
            guild_id = event.player.guild_id
            if event.player.guild_id in self._jockeys:
                await self._jockeys[guild_id].handle_event(event)
        else:
            # Must be either a NodeConnectedEvent or a NodeDisconnectedEvent.
            if isinstance(event, NodeConnectedEvent):
                print('Connected to Lavalink node.')
            elif isinstance(event, NodeDisconnectedEvent):
                print('Disconnected from Lavalink node.')
    
    def delete_jockey(self, guild: int):
        if guild in self._jockeys:
            del self._jockeys[guild]

    def get_jockey(self, guild: int) -> Jockey:
        # Create jockey for guild if it doesn't exist yet
        if guild not in self._jockeys:
            self._jockeys[guild] = Jockey(
                guild=guild,
                db=self._db,
                bot=self._bot,
                player=self._bot.lavalink.player_manager.create(guild),
                spotify=self.spotify_client
            )
        
        return self._jockeys[guild]

    @slash_command(name='play', description='Play a song from a search query or a URL.')
    async def play(self, interaction: Interaction, query: Optional[str] = None):
        """
        Play a song.
        """
        # Throw error if no query was provided
        if query == None:
            return await interaction.response.send_message(embed=create_error_embed('No query provided. To unpause, use the `unpause` command.'))

        # Dispatch to jockey
        await interaction.response.defer()
        jockey = self.get_jockey(interaction.guild_id)
        await jockey.play(interaction, query)
