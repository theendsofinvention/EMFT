# coding=utf-8

import warnings

# I'm importing transitions here since it resets the global Python warning filter
# noinspection PyUnresolvedReferences
import transitions  # noqa: F401

warnings.resetwarnings()

warnings.filterwarnings('ignore',
                        category=DeprecationWarning,
                        message='Non-string (usernames|passwords) will no longer be supported in Requests 3.0.0',
                        module='requests')

warnings.filterwarnings('ignore',
                        category=DeprecationWarning,
                        message='the imp module is deprecated in favour of importlib',
                        module='pywintypes')

warnings.filterwarnings('ignore',
                        category=DeprecationWarning,
                        message="generator '_sep_inserter' raised StopIteration",
                        module='natsort')

warnings.filterwarnings('ignore',
                        category=ImportWarning,
                        message="Not importing directory .*sphinxcontrib",
                        module='importlib')

warnings.filterwarnings('ignore',
                        category=ImportWarning,
                        message="Not importing directory .*ruamel",
                        module='importlib')

warnings.filterwarnings('ignore',
                        category=ResourceWarning,
                        message=r"unclosed \<ssl\.SSLSocket ",
                        )

warnings.filterwarnings('ignore',
                        category=DeprecationWarning,
                        message=r"Report\.file_reporters will no longer be available",
                        module='coverage',
                        )

warnings.filterwarnings('ignore',
                        category=ImportWarning,
                        message=r"Not importing directory.*sphinxjp",
                        )
