#!/usr/bin/env python

import os
import re
import sys

import params

params = params.parseParams()
prompt, usage = params["promptString"], params["usage"]
if usage:
    params.usage()


def execute_command(command):
    try:
        os.execve(command, args, os.environ)
    except FileNotFoundError:
        print(f"{args[0]}: command not found")
        sys.exit(1)


def find_command(command):
    for path in os.environ["PATH"].split(os.pathsep):
        full_command = os.path.join(path, command)
        if os.path.exists(full_command) and os.access(full_command, os.X_OK):
            return full_command
    return None


def main():
    try:
        while True:
            # Print the prompt
            # print(os.getcwd()) # Print the current working directory
            sys.stdout.write(prompt)
            sys.stdout.flush()

            # Read command from user
            input_line = sys.stdin.readline().strip()
            if not input_line:
                break
            command, *args = input_line.split()

            # Built-in commands
            if command == "exit":
                break
            elif command == "cd":
                try:
                    os.chdir(args[0])
                except Exception as e:
                    print(f"cd: {e}")
                continue

            # Find command in PATH
            full_command = find_command(command)
            if not full_command:
                print(f"{command}: command not found")
                continue

            # fork - exec if program if already exists in pc: echo, cat, ls, etc
            pid = os.fork()
            if pid == 0:
                # Child process
                execute_command(full_command, *args)
            else:
                # Parent process
                os.waitpid(pid, 0)
    except KeyboardInterrupt:
        print("\nInterrupted")


if __name__ == "__main__":
    main()
