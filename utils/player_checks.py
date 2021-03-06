from nextcord import Interaction
from .exceptions import VoiceCommandError


def check_mutual_voice(itx: Interaction) -> bool:
    """ This check ensures that the bot and command author are in the same voice channel. """
    # Check that the user is in a voice channel in the first place.
    if itx.guild is not None:
        if not itx.user.voice or not itx.user.voice.channel:
            raise VoiceCommandError('Join a voice channel first.')
    else:
        # Not allowed in DMs
        raise VoiceCommandError('You can only use this command in a server.')

    player = itx.client.lavalink.player_manager.get(itx.guild.id)
    if player is None:
        if itx.application_command.name == 'play':
            # The /play command causes the bot to connect to voice,
            # so we don't have to worry about the rest of the checks here.
            return True
        raise VoiceCommandError('Please `/play` something first before using this command.')

    vc = itx.user.voice.channel
    if not player.is_connected:
        # Bot needs to already be in voice channel to pause, unpause, skip etc.
        if itx.application_command.name != 'play':
            raise VoiceCommandError('I\'m not connected to voice.')

        # Bot needs to have permissions to connect to voice.
        permissions = vc.permissions_for(itx.guild.me)
        if not permissions.connect or not permissions.speak:
            raise VoiceCommandError('I need the `CONNECT` and `SPEAK` permissions to play music.')

        # Bot needs to connect to a channel that isn't full.
        if vc.user_limit and vc.user_limit <= len(vc.members):
            raise VoiceCommandError('Your voice channel is full.')
    else:
        if int(player.channel_id) != vc.id:
            raise VoiceCommandError('You need to be in my voice channel.')
    
    return True
