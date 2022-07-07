from typing import List, Tuple, Callable, Union, Any
import json
import sys
import logging
import structlog

from logger_cloudwatch_structlog.custom_processors import AWSCloudWatchLogs, PasswordCensor

# This is from https://github.com/openlibraryenvironment/serverless-zoom-recordings
_NOISY_LOG_SOURCES = ("boto", "boto3", "botocore")


def setup_logging(wordlist_to_censor: List = None,
                  callouts: List = None,
                  processors: List = None,
                  serializer: Callable[..., Union[str, bytes]] = json.dumps,
                  level: int = logging.INFO,
                  noisy_log_sources: Tuple = _NOISY_LOG_SOURCES,
                  **serializer_kw):
    """
    Configure logging for the application.

    Args:
        wordlist_to_censor: (List | None, optional) List with words to be censored in the event_dict, if they
                            are present. Defaults to None.
        callouts: (List | None, optional) Are printed in clear-text on the front of the log line. Only the first two
                 items of this list are called out. Defaults to None.
        processors: (List | None, optional) A list of log processors. A log processor is a regular callable, the return
                   value of each processor is passed on to the next one as event_dict until finally the return value of
                   the last processor gets passed into the wrapped logging method. Defaults to a one-fits-all solution,
                   but if you need something different, you can change it.
        callouts (List | None, optional): Are printed in clear-text on the front of the log line. Only the first two
                 items of this list are called out.
        serializer: (Callable[..., Union[str, bytes]], optional): A :func:`json.dumps`-compatible callable that will be
                    used to format the string. Defaults to json.dumps.
        level: (int, optional) Sets the threshold for this logger to level. Logging messages which are less severe than
               level will be ignored. Defaults to logging.INFO.
        noisy_log_sources (Tuple | None, optional): Tuple of sources that output a lot of unnecessary messages. Defaults
                          to _NOISY_LOG_SOURCES.
        **serializer_kw: Arbitrary keyword arguments. Are passed unmodified to *serializer*. If *default* is passed, it
            will disable support for ``__structlog__``-based serialization.
    """

    if processors is None:
        processors = [
            # If log level is too low, abort pipeline and throw away log entry.
            structlog.stdlib.filter_by_level,
            # Add log level to event dict.
            structlog.stdlib.add_log_level,
            # Perform %-style formatting.
            structlog.stdlib.PositionalArgumentsFormatter(),
            # Add a timestamp in ISO 8601 format.
            structlog.processors.TimeStamper(fmt="iso"),
            # If the "stack_info" key in the event dict is true, remove it and
            # render the current stack trace in the "stack" key.
            structlog.processors.StackInfoRenderer(),
            # If the "exc_info" key in the event dict is either true or a
            # sys.exc_info() tuple, remove "exc_info" and render the exception
            # with traceback into the "exception" key.
            structlog.processors.format_exc_info,
            # If some value is in bytes, decode it to a unicode str.
            structlog.processors.UnicodeDecoder(),
            # Censor the words
            PasswordCensor(wordlist=wordlist_to_censor),
            # Merge in a global (thread-local) context.
            structlog.threadlocal.merge_threadlocal,
            # Render the final event dict as JSON.
            AWSCloudWatchLogs(callouts=callouts, serializer=serializer, **serializer_kw),
        ]

    # This is from https://github.com/openlibraryenvironment/serverless-zoom-recordings
    # Structlog configuration
    structlog.configure(
        processors=processors,
        context_class=dict,
        # `wrapper_class` is the bound logger that you get back from
        # get_logger(). This one imitates the API of `logging.Logger`.
        wrapper_class=structlog.stdlib.BoundLogger,
        # `logger_factory` is used to create wrapped loggers that are used for
        # OUTPUT. This one returns a `logging.Logger`. The final value (a JSON
        # string) from the final processor (`JSONRenderer`) will be passed to
        # the method of the same name as that you've called on the bound logger.
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Effectively freeze configuration after creating the first bound
        # logger.
        cache_logger_on_first_use=True,
    )

    # This is from https://github.com/openlibraryenvironment/serverless-zoom-recordings
    # Stdlib logging configuration. `force` was added to reset the AWS-Lambda-supplied log handlers.
    # see: https://stackoverflow.com/questions/37703609/using-python-logging-with-aws-lambda#comment120413034_45624044
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
        force=True,
    )
    for source in noisy_log_sources:
        logging.getLogger(source).setLevel(logging.WARNING)


def get_logger(*args: Any, **initial_values: Any) -> Any:
    """
    Convenience function that returns a structlog logger

    Args:
        args: (Any, optional): Positional arguments that are passed unmodified to the logger factory. Therefore,
        it depends on the factory what they mean.
        initial_values: (Any, optional): Values that are used to pre-populate the context.

    Returns: A proxy that creates a correctly configured bound logger when necessary. We are using the default bound
             logger `structlog.stdlib.BoundLogger`.
    """

    return structlog.get_logger(*args, **initial_values)


def setup_and_get_logger(**kwargs):

    """
    Configure logging for the application and return the logger. This function is a one-fits-all solution with some
    possibilities to change the setup. But you cannot add keyword arguments for the logger factory or even values that
    are used to pre-populate the context. If you need a more flexible solution, you can call setup_logging() and
    get_logger() separated.

    Returns: A proxy that creates a correctly configured bound logger when necessary.
    """

    # Check if we have the arguments for the setup. If they are not present, we use a one-fits-all solution.
    wordlist_to_censor = kwargs.pop('wordlist_to_censor', None)
    callouts = kwargs.pop('callouts', ["status_code", "event"])
    processors = kwargs.pop('processors', None)
    serializer = kwargs.pop('serializer', json.dumps)
    level = kwargs.pop('level', logging.INFO)
    noisy_log_sources = kwargs.pop('noisy_log_sources', _NOISY_LOG_SOURCES)
    sort_keys = kwargs.pop('sort_keys', False)

    setup_logging(wordlist_to_censor=wordlist_to_censor, callouts=callouts, processors=processors,
                  serializer=serializer, level=level, noisy_log_sources=noisy_log_sources, sort_keys=sort_keys,
                  **kwargs)

    return get_logger()
