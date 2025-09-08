import asyncio
import json
from pathlib import Path

from rich.json import JSON

from textual_autocomplete import AutoComplete as BaseAutoComplete
from textual_autocomplete._autocomplete import DropdownItem, TargetState

from textual.screen import ModalScreen
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.containers import Grid
from textual.widgets import Input, Button, Markdown, Label
from textual import work

class QuitScreen(ModalScreen):
    """Screen with a dialog to quit."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit?", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()
