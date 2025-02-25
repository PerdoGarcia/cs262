from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateRequest(_message.Message):
    __slots__ = ("username", "password")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    username: str
    password: str
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class CreateReply(_message.Message):
    __slots__ = ("success", "errorMessage")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    errorMessage: str
    def __init__(self, success: bool = ..., errorMessage: _Optional[str] = ...) -> None: ...

class LoginRequest(_message.Message):
    __slots__ = ("username", "password")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    username: str
    password: str
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class LoginReply(_message.Message):
    __slots__ = ("success", "errorMessage")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    errorMessage: str
    def __init__(self, success: bool = ..., errorMessage: _Optional[str] = ...) -> None: ...

class LogoutRequest(_message.Message):
    __slots__ = ("username",)
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class LogoutReply(_message.Message):
    __slots__ = ("success", "errorMessage")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    errorMessage: str
    def __init__(self, success: bool = ..., errorMessage: _Optional[str] = ...) -> None: ...

class ListAccountsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListAccountsReply(_message.Message):
    __slots__ = ("success", "accounts")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ACCOUNTS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    accounts: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, success: bool = ..., accounts: _Optional[_Iterable[str]] = ...) -> None: ...

class SendMessageRequest(_message.Message):
    __slots__ = ("fromUser", "toUser", "time", "message")
    FROMUSER_FIELD_NUMBER: _ClassVar[int]
    TOUSER_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    fromUser: str
    toUser: str
    time: str
    message: str
    def __init__(self, fromUser: _Optional[str] = ..., toUser: _Optional[str] = ..., time: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class SendMessageReplyToSender(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class SendMessageReplyToLoggedInReceiver(_message.Message):
    __slots__ = ("success", "messageId", "fromUser", "time", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    FROMUSER_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    messageId: int
    fromUser: str
    time: str
    message: str
    def __init__(self, success: bool = ..., messageId: _Optional[int] = ..., fromUser: _Optional[str] = ..., time: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class ReadMessagesRequest(_message.Message):
    __slots__ = ("username", "numMessages")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    NUMMESSAGES_FIELD_NUMBER: _ClassVar[int]
    username: str
    numMessages: int
    def __init__(self, username: _Optional[str] = ..., numMessages: _Optional[int] = ...) -> None: ...

class ReadMessagesReply(_message.Message):
    __slots__ = ("success", "numRead", "messages")
    class Message(_message.Message):
        __slots__ = ("messageId", "fromUser", "time", "message")
        MESSAGEID_FIELD_NUMBER: _ClassVar[int]
        FROMUSER_FIELD_NUMBER: _ClassVar[int]
        TIME_FIELD_NUMBER: _ClassVar[int]
        MESSAGE_FIELD_NUMBER: _ClassVar[int]
        messageId: int
        fromUser: str
        time: str
        message: str
        def __init__(self, messageId: _Optional[int] = ..., fromUser: _Optional[str] = ..., time: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    NUMREAD_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    success: bool
    numRead: int
    messages: _containers.RepeatedCompositeFieldContainer[ReadMessagesReply.Message]
    def __init__(self, success: bool = ..., numRead: _Optional[int] = ..., messages: _Optional[_Iterable[_Union[ReadMessagesReply.Message, _Mapping]]] = ...) -> None: ...

class DeleteMessagesRequest(_message.Message):
    __slots__ = ("username", "messageId")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    username: str
    messageId: int
    def __init__(self, username: _Optional[str] = ..., messageId: _Optional[int] = ...) -> None: ...

class DeleteMessagesReply(_message.Message):
    __slots__ = ("success", "errorMessage")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    errorMessage: str
    def __init__(self, success: bool = ..., errorMessage: _Optional[str] = ...) -> None: ...

class DeleteAccountRequest(_message.Message):
    __slots__ = ("username", "messageId")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    username: str
    messageId: int
    def __init__(self, username: _Optional[str] = ..., messageId: _Optional[int] = ...) -> None: ...

class DeleteAccountReply(_message.Message):
    __slots__ = ("success", "errorMessage")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    errorMessage: str
    def __init__(self, success: bool = ..., errorMessage: _Optional[str] = ...) -> None: ...
