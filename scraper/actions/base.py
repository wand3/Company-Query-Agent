#!/usr/bin/env python3
"""
    Using the command pattern of software design
"""


class Base:
    """
        A base class that all commands will inherit from
    """

    def execute(self):
        pass


class linkednController:
    """
        takes a list of commands and executes them sequentially
    """
    def __init__(self):
        # self.page = page
        self.commands = []

    def add_command(self, command: Base):
        self.commands.append(command)

    async def execute_commands(self):
        all_results = []
        for command in self.commands:
            result = await command.execute()
            if result:  # If the command returns something (e.g., a list of links)
                all_results.extend(result)
            return all_results

    def clear_commands(self):
        """Optional method to clear commands between executions."""
        self.commands = []
