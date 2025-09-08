from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll, Grid
from textual.widgets import Button, Input, Markdown, Label, Static
from textual_autocomplete import AutoComplete as BaseAutoComplete
from textual_autocomplete._autocomplete import DropdownItem, TargetState

import json
import pandas as pd
from pathlib import Path

class CustomAutoComplete(BaseAutoComplete):
    def apply_completion(self, value: str, state: TargetState) -> None:
        """Apply the completion to the target widget."""
        self.log(f"Applying completion with value: {value}")
        if isinstance(self.target, Input):
            # Update the input value
            self.target.value = value
            self.target.cursor_position = len(value)
            # Create and post a proper Input.Changed event
            message = Input.Changed(self.target, value=value)
            # self.target.post_message(message)
            # Also notify the parent app
            self.app.post_message(message)
        # Hide dropdown after selection
        self.display = False