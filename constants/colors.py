from colorama import Fore, init

__all__ = ["GREEN", "LGREEN", "RESET", "LYELLOW", "LBLUE", "CYAN"]

init(convert=True, autoreset=True)

GREEN: str = Fore.GREEN
LGREEN: str = Fore.LIGHTGREEN_EX
RESET: str = Fore.RESET
LYELLOW: str = Fore.LIGHTYELLOW_EX
LBLUE: str = Fore.LIGHTBLUE_EX
CYAN: str = Fore.CYAN
RED: str = Fore.RED
LRED: str = Fore.LIGHTRED_EX
