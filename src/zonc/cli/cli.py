import sys
from .cmd_zonc import cmd_zon_run, cmd_zon_version, cmd_zon_help, cmd_zon_set_path, cmd_zon_show_path, cmd_zon_clear_path
from .cmd_zonc import cmd_zon_set_file

def run_cli():
    args = sys.argv[1:]
    if len(args) == 0:
        print("[zon error]: No command or file specified.")
        print("-- The forge is idle. Use zon help to learn the commands and start building.")
        return
    
    if args[0] == "r":
        if len(args) < 2:
            print("[zon error]: No file specified for the run command.")
            print("-- The engine needs a target. Use zon r <filename>.zon to start execution.")
            return
        
        cmd_zon_run(args[1])
    
    elif args[0] == "vers":
        cmd_zon_version()
        
    elif args[0] == "help":
        params = args[1:]
        if len(params) > 0:
            cmd_zon_help(params[0])
            return
        
        cmd_zon_help()
        return
    
    elif args[0] == "setpath":
        path = args[1:]
        if len(path) < 1:
            print("[zon error]: No path provided for setpath.")
            print("-- Usage: zon setpath /path/to/your/scripts")
            return
        
        cmd_zon_set_path(path[0])
        
    elif args[0] == "showpath":
        cmd_zon_show_path()
        
    elif args[0] == "clrpath":
        cmd_zon_clear_path()
        
    elif args[0] == "setfile":
        path = args[1:]
        if len(path) < 1:
            print("[zon error]: No path or filename specified.")
            print("-- Usage: zon setfile path/to/folder/script.zon")
            return
        
        cmd_zon_set_file(path[0])
        
    elif args[0] == "repl":
        cmd_zon_set_file(mode=1)
        
    elif args[0] == "tokens":
        if len(args) < 2:
            print("[zon error]: No file specified for the tokens command.")
            print("-- The engine needs a target. Use zon tokens <filename>.zon to start execution.")
            return
        
        cmd_zon_run(args[1], "token")
        
    elif args[0] == "ast":
        if len(args) < 2:
            print("[zon error]: No file specified for the ast command.")
            print("-- The engine needs a target. Use zon ast <filename>.zon to start execution.")
            return
        
        cmd_zon_run(args[1], "ast")
        
    elif args[0] == "sem":
        if len(args) < 2:
            print("[zon error]: No file specified for the semantic command.")
            print("-- The engine needs a target. Use zon sem <filename>.zon to start execution.")
            return
        
        cmd_zon_run(args[1], "smt")
        
    else:
        print("[zon error]: Unknown command.")
        print("-- The forge doesn't recognize that instruction. Use zon help to see the available commands.")