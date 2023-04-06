"""Bot module"""


class BotMode:
    modes = (
        POLLING,
        WEBHOOK,
    ) = range(2)
