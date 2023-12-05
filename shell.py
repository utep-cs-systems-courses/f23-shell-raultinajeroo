#!/usr/bin/env python

import os
import re
import sys

import params

params = params.parseParams()
prompt, usage = params["promptString"], params["usage"]
if usage:
    params.usage()


def execute_command(command, *args):
    try:
        os.execve(command, [command] + list(args), os.environ)
    except FileNotFoundError:
        print(f"{args[0]}: command not found")
        sys.exit(1)


def find_command(command):
    for path in os.environ["PATH"].split(os.pathsep):
        full_command = os.path.join(path, command)
        if os.path.exists(full_command) and os.access(full_command, os.X_OK):
            return full_command
    return None


def processInput():
    # Print prompt
    sys.stdout.write(prompt)
    sys.stdout.flush()

    # Read command from user
    input_line = sys.stdin.readline()
    if not input_line:
        return None

    # Split by pipes
    cmds = [cmd.strip() for cmd in input_line.split('|')]

    parsed_cmds = []
    for cmd in cmds:
        # Split by redirection
        parts = re.split(r'([<>])', cmd)
        parsed = [part.strip() for part in parts]
        
        # Split command and args
        command, *args = parsed[0].split()
        parsed_cmds.append((command, args, parsed[1:]))
    return parsed_cmds


def redirect_io(redir):
    for i in range(0, len(redir), 2):
        direction, file = redir[i], redir[i+1]
        if direction == '>':
            # Output redirection
            fd = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            os.dup2(fd, 1)  # Redirect stdout to file
            os.close(fd)
        elif direction == '<':
            # Input redirection
            fd = os.open(file, os.O_RDONLY)
            os.dup2(fd, 0)  # Redirect stdin to file
            os.close(fd)

def shell():
    while True:
        parsed_cmds = processInput()
        cmd_count = len(parsed_cmds)

        for i, (command, args, redir) in enumerate(parsed_cmds):
            # Built-in commands
            if command == "exit":
                sys.exit(0)
            elif command == "cd":
                try:
                    os.chdir(args[0])
                except NameError as e:
                    print(f"cd: {e}")
                continue

            # Set up pipes for next commandss
            if i < cmd_count - 1:
                r, w = os.pipe()

            pid = os.fork()
            if pid == 0: # Child
                # Set pipe's stdin / stdout
                if i > 0:
                    os.dup2(prev_r, 0)
                    os.close(prev_r)
                if i < cmd_count - 1:
                    os.dup2(w, 1)
                    os.close(r)
                    os.close(w)

                # Handle redirections
                try:
                    redirect_io(redir)
                except (IOError, IndexError) as e:
                    print(e)
                    break

                # Execute command
                full_command = find_command(command)
                if not full_command:
                    print(f"{command}: command not found")
                    sys.exit(1)
                execute_command(full_command, *args)
            else: # Parent
                if i > 0:
                    os.close(prev_r)
                if i < cmd_count - 1:
                    os.close(w)
                    prev_r = r
                os.waitpid(pid, 0)

def main():
    try:
        shell()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt")
        sys.exit(1)

if __name__ == "__main__":
    main()