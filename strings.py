# This is the regex that is used to determine if a stream is an 'AA stream'.
TITLE_REGEX = r'(\baa\b|advancements|todos los logro)'

# This is the string printed by /streambot_help
HELP_STRING = f"""***StreamRoleBot FAQ / Help***

StreamRoleBot automatically gives users the Streaming role if their stream title matches the following case-insensitive regex: `{TITLE_REGEX}`.

StreamRoleBot additionally provides a `/live` command that can set a user to live even if their title does not match the regex. The 'Streaming' role will remain until that user stops streaming.

These features rely on Discord activity status in order to ensure:
- That users will have the role properly/automatically removed when they go offline
- That other users can access your stream by clicking on your name -> 'watch'

***FAQ***

**Discord cannot tell that I am streaming (I don't see the purple activity icon)**

This is usually caused by not having 'Streamer Mode' enabled in Discord. Streamer Mode disables some notifications while active but is otherwise mostly harmless. You can activate this or set it up to activate automatically in Settings > Streamer Mode.

**Discord shows me as live (I see the purple activity icon) but `/streambot_debug` does not list me as a detected 'live' server member.**

This can be caused by a variety of issues. Check the following:
- That you do not have server-specific privacy settings enabled for activities
- That you do not have general privacy settings enabled for activities
- That your stream title is not more than 128 characters long

**I want to put AA in my title without being assigned the role.**

Put !nobot in your stream title.
"""

# Example activity updates.
"""
Logged in as StreamRoleBot#3286 (ID:)
(<CustomActivity name='C++ folder' emoji=<PartialEmoji animated=False name='📁' id=None>>,)
(<CustomActivity name='C++ folder' emoji=<PartialEmoji animated=False name='📁' id=None>>, <Streaming name='NON EXISTENT STREAM JUST TESTING SOMETHING SORRY'>)
(<CustomActivity name='C++ folder' emoji=<PartialEmoji animated=False name='📁' id=None>>,)
"""
