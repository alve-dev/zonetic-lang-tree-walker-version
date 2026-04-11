from dataclasses import dataclass

@dataclass
class Native:
    func: callable

def _print(arg):
    len_args = len(arg)
    for i, p in enumerate(arg):
        if isinstance(p, bool): p = str(p).lower()
        print(p, end='')
        if i != len_args-1:
            print(" ", end='')
    print()
            
def _read_int(prompt) -> int:
    return int(input(*prompt))

def _read_float(prompt) -> float:
    return float(input(*prompt))

def _read_string(prompt) -> str:
    return input(*prompt)