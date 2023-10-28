from enum import StrEnum


class MessageType(StrEnum):
    OPENED = "opened"
    GET_READY = "get_ready"


class MessageParser:
    def __init__(self, message: str) -> None:
        self._message = message

        if self._get_message_type():
            self._parse()

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    def _get_message_type(self) -> bool:
        if self._message.find("Get Ready") >= 0:
            self._message_type = MessageType.GET_READY
            self._is_valid = True
        elif self._message.find("𝘖𝘱𝘦𝘯𝘦𝘥") >= 0:
            self._message_type = MessageType.OPENED
            self._is_valid = True
        else:
            self._is_valid = False

        return self._is_valid

    def _parse(self) -> None:
        pass
