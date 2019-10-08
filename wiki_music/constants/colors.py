"""Defines aliases for colorama color constrants to be used in whole package.
"""

from colorama import Fore, init

__all__ = ["GREEN", "LGREEN", "RESET", "YELLOW", "LBLUE", "CYAN"]

init(convert=True, autoreset=True)

GREEN: str = Fore.GREEN  #: used to higlight important messages in CLI mode
LGREEN: str = Fore.LIGHTGREEN_EX  #: highlight less important messages in CLI mode
RESET: str = Fore.RESET  #: resets the foreground color to default
YELLOW: str = Fore.YELLOW  #: used to highlight warnings in CLI mode
LBLUE: str = Fore.LIGHTBLUE_EX  #: used to highlight found files in CLI mode
CYAN: str = Fore.CYAN  #: used to designate user input is needed in CLI mode
RED: str = Fore.RED  #: uused to highlight errors in CLI mode
