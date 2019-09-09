import enum


class State(enum.Enum):
    """
    Child process lifecycle
    """
    INITIALIZING = b'\x00'
    INITIALIZED = b'\x01'
    WAIT_EXEC_DATA = b'\x02'
    BOOTING = b'\x03'
    STARTED = b'\x04'
    EXECUTING = b'\x05'
    STOPPING = b'\x06'
    FINISHED = b'\x07'

    def as_int(self) -> int:
        return self.value[0]

    def is_next(self, other: 'State') -> bool:
        return other.as_int() == self.as_int() + 1

    def is_on_or_after(self, other: 'State') -> bool:
        return self.value[0] >= other.value[0]

    def is_before(self, other: 'State') -> bool:
        return self.value[0] < other.value[0]
