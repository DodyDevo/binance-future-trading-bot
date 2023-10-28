from enum import StrEnum


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
