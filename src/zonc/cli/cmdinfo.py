from dataclasses import dataclass, field
from typing import List

@dataclass
class Flag:
    name: str
    description: str

@dataclass
class CmdArg:
    name: str
    description: str

@dataclass
class CmdInfo:
    area: str
    summary: str
    category: str
    usage: str
    args: List[CmdArg] = field(default_factory=list)
    flags: List[Flag] = field(default_factory=list)

    def show_help(self):
        print(f"HELP: Area '{self.area}' ({self.summary})")
        print(f"Usage: {self.usage}\n")
        print("Flags:")
        for f in self.flags:
            print(f"    {f.name:<12} {f.description}")
            
