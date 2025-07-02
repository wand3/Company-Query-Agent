#!/usr/bin/env python3
"""
    Using the command pattern of software design
"""
import asyncio
from contextlib import asynccontextmanager
from playwright.async_api import Page
from .handlers.handle_popups import UnexpectedPopupHandler


class Base:
    """
        A base class that all commands will inherit from

        Enhanced base class with context management and popup handling
    """

    def __init__(self, page: Page = None):
        self.page = page
        self.popup_handler = None

    async def __aenter__(self):
        """Initialize popup handler when command starts"""
        if self.page:
            self.popup_handler = UnexpectedPopupHandler(self.page)
            await self.popup_handler.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Cleanup popup handler when command completes"""
        if self.popup_handler:
            await self.popup_handler.stop()

    @asynccontextmanager
    async def disable_popups(self):
        """Temporarily disable popup handling within a command"""
        if self.popup_handler:
            original_state = self.popup_handler.enabled
            self.popup_handler.enabled = False
            try:
                yield
            finally:
                self.popup_handler.enabled = original_state
        else:
            yield  # No-op if no handler

    async def execute(self):
        """Main command logic to be implemented by subclasses"""
        raise NotImplementedError("Commands must implement execute()")


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
