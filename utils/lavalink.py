from asyncio import sleep
from nextcord import Client, StageChannel, VoiceChannel, VoiceClient
from lavalink import Client
from typing import Dict, List, Union


def init_lavalink(id: int, nodes: List[Dict[str, str]], timeout: int) -> Client: 
    client = Client(id)

    # Check that our inactivity timeout is valid
    if timeout < 1:
        raise ValueError('$INACTIVE_SEC must be an integer greater than 0')

    # Add local node
    for node in nodes:
        client.add_node(
            host=node['server'],
            port=node['port'],
            password=node['password'],
            region=node['region'],
            resume_key=node['id'],
            resume_timeout=timeout,
            name=node['id']
        )

    return client


class LavalinkVoiceClient(VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    https://discordpy.readthedocs.io/en/latest/api.html#voiceprotocol

    Originally from https://github.com/tailoric/Lavalink.py/commit/11124bd3ac17423520594adaf66b3950775b58f5
    """

    def __init__(self, client: Client, channel: Union[StageChannel, VoiceChannel]):
        self.client = client
        self.channel = channel

        # Ensure there exists a client already
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = init_lavalink(client.user.id)
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        # The data needs to be transformed before being handed down to voice_update_handler
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        # The data needs to be transformed before being handed down to voice_update_handler
        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        # Ensure there is a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_deaf=True)
        return await sleep(1)

    async def disconnect(self, *, force: bool = False) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that
        # would set channel_id to None doesn't get dispatched after the 
        # disconnect
        player.channel_id = None
        self.cleanup()
