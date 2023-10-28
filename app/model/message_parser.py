from enum import StrEnum

from service import setting as Setting


class MessageType(StrEnum):
    OPENED = "OPENED"
    GET_READY = "GET_READY"
    OTHER = "OTHER"


class SideType(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class MessageParser:
    def __init__(self, message: str) -> None:
        self._message = message

        self._get_message_type()

        if self._message_type == MessageType.GET_READY:
            self._parse()

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    @property
    def message_type(self) -> MessageType:
        return self._message_type

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def side(self) -> SideType:
        return self._side

    @property
    def entry(self) -> float:
        return self._entry

    @property
    def target(self) -> float:
        return self._target

    @property
    def stop(self) -> float:
        return self._stop

    def _get_message_type(self) -> None:
        if self._message.find("Get Ready") >= 0:
            self._message_type = MessageType.GET_READY
            self._is_valid = True
        elif self._message.find("𝘖𝘱𝘦𝘯𝘦𝘥") >= 0:
            self._message_type = MessageType.OPENED
            self._is_valid = True
        else:
            self._message_type = MessageType.OTHER
            self._is_valid = False

    def _parse(self) -> None:
        message_lines = list(filter(None, self._message.split("\n")))
        self._symbol = message_lines[0][
            message_lines[0].index("#") + 1 : message_lines[0].index(".P")
        ]
        self._side = (
            SideType.BUY if message_lines[0].find("𝗟𝗢𝗡𝗚") >= 0 else SideType.SELL
        )
        self._entry = float(
            message_lines[1][
                message_lines[1].index(":")
                + 2 : message_lines[1].index(" (𝙨𝙪𝙗𝙟𝙚𝙘𝙩 𝙩𝙤 𝙘𝙝𝙖𝙣𝙜𝙚)")
            ]
        )
        self._target = float(
            message_lines[Setting.TARGET + 2][
                message_lines[Setting.TARGET + 2].index(":") + 2 :
            ]
        )
        self._stop = float(message_lines[9][message_lines[9].index(":") + 2 :])
