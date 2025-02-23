from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

commands = ['help', 'ports', 'setport', 'setbaud', 'connect', 'disconnect', 'loadjson', 'loadtxt', 'list', 'send', 'sendall', 'echo', 'savlog', 'exit']
command_completer = WordCompleter(commands, ignore_case=True)
session = PromptSession()

while True:
    try:
        user_input = session.prompt(">> ", completer=command_completer)
        if user_input.strip().lower() == "exit":
            break
        # Process the command here...
        print(f"You entered: {user_input}")
    except KeyboardInterrupt:
        continue
    except EOFError:
        break
