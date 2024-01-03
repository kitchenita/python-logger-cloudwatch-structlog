import json
from typing import List, Dict
from structlog.processors import _json_fallback_handler
from structlog.typing import Any, Callable, EventDict, Union, WrappedLogger


class AWSCloudWatchLogs:
    """This class is from https://github.com/openlibraryenvironment/serverless-zoom-recordings

    Render a log line compatible with AWS CloudWatch Logs.  This is a copy and modification of
    `structlog.processors.JSONRenderer`. Render the ``event_dict`` using ``serializer(event_dict, **json_kw)``.

    Args:
        callouts (List | None, optional): Are printed in clear-text on the front of the log line. Only the first two
            items of this list are called out. Defaults to None.
        serializer (Callable[..., Union[str, bytes]], optional): A :func:`json.dumps`-compatible callable that will be
            used to format the string.  This can be used to use alternative JSON encoders like `simplejson
            <https://pypi.org/project/simplejson/>`_ or `RapidJSON <https://pypi.org/project/python-rapidjson/>`_
            (faster but Python 3-only). Default: :func:`json.dumps`.
        **dumps_kw: Arbitrary keyword arguments. Are passed unmodified to *serializer*. If *default* is passed, it
            will disable support for ``__structlog__``-based serialization.

        """

    def __init__(self, callouts: List = None, serializer: Callable[..., Union[str, bytes]] = json.dumps,
                 **dumps_kw: Any,) -> None:
        try:
            self._callout_one_key = callouts[0]
        except (IndexError, TypeError):
            self._callout_one_key = None
        try:
            self._callout_two_key = callouts[1]
        except (IndexError, TypeError):
            self._callout_two_key = None
        dumps_kw.setdefault("default", _json_fallback_handler)
        self._dumps_kw = dumps_kw
        self._dumps = serializer

    def __call__(self, _, name: str, event_dict: EventDict) -> Union[str, bytes]:
        """The return type of this depends on the return type of self._dumps."""

        header = f'[{name.upper()}] '
        callout_one = event_dict.get(self._callout_one_key, None)
        callout_two = event_dict.get(self._callout_two_key, None)

        if callout_one:
            header += f'"{callout_one}" '
        if callout_two:
            header += f'"{callout_two}" '

        return header + self._dumps(event_dict, **self._dumps_kw)


class PasswordCensor:
    """
    Censor words in ``event_dict``.

    callouts (List | None, optional)

    Args:
        wordlist: (List | None, optional) List with words to be censored in the event_dict, if they are
                  present. Defaults to None.

    """

    __slots__ = ("_censor", "_wordlist")

    def __init__(self, wordlist: List = None) -> None:

        self._wordlist = wordlist
        self._censor = _make_censor(wordlist)

    def __call__(self, logger: WrappedLogger, name: str, event_dict: EventDict) -> EventDict:
        return self._censor(event_dict)

    def __getstate__(self) -> Dict[str, Any]:
        return {"wordlist": self._wordlist}

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self._wordlist = state["wordlist"]

        self._censor = _make_censor(**state)


def _make_censor(wordlist: List) -> Callable[[EventDict], EventDict]:
    """
    Create a censor function

    Args:
        wordlist (List | None): List with words to be censored in the event_dict if they are present

    Returns:
        Callable: Function that censor words from an EventDict.

    Raises:
        ValueError: If wordlist is not a tuple or a list.

    """
    if wordlist is None:

        def nothing_to_do(event_dict: EventDict) -> EventDict:
            return event_dict

        return nothing_to_do

    if not (type(wordlist) is tuple) and not (type(wordlist) is list):
        raise ValueError("The wordlist must be a tuple or a list")

    def censor_every_word(event_dict: EventDict) -> EventDict:

        for key in wordlist:
            pw = event_dict.get(key)

            if pw:
                event_dict[key] = "*CENSORED*"

        return event_dict

    return censor_every_word
