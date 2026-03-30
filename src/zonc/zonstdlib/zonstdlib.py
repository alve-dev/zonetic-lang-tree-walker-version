from dataclasses import dataclass

@dataclass
class Native:
    func: callable

def _print(arg):
    print(*arg)
   
def _read_int(prompt) -> int:
    return int(input(*prompt))

def _read_float(prompt) -> float:
    return float(input(*prompt))

def _read_string(prompt) -> str:
    return input(*prompt)