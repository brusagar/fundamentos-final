import asyncio
import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Grid, Vertical, Horizontal
from textual.widgets import Input, Markdown, Button, Label, Select

from utils.quit_screen import QuitScreen
from textual import work
from components.sentence_editor import NEREditorScreen
from components.spert_trainer import SpertTrainerScreen
from components.spert_predictor import SpertPredictorScreen
from components.script_executor import ScriptExecutorScreen
from components.entity_search import EntitySearchScreen
from components.text_preprocessor import TextPreprocessorScreen
from typing import Dict, Set


class App(App):
    """NLP Application Toolkit - Main interface for text processing and analysis tools."""

    CSS_PATH_2 = "modal01.tcss"
    BINDINGS = [("q", "request_quit", "Quit")]
    CSS_PATH = "dictionary.tcss"
    DATA_PATH = Path("data.json")
    
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="main-menu"):
            yield Label("NLP Application Toolkit", id="app-title")
            yield Label("Select a tool to get started:", id="subtitle")
            
            with Horizontal(classes="menu-item"):
                yield Button("Raw Text Processor", id="preprocessor", variant="warning")
                yield Label("Convert and chunk text files for processing", classes="description")
            
            with Horizontal(classes="menu-item"):
                yield Button("Spacy Pipeline", id="executor", variant="primary")
                yield Label("Run spacy processing pipeline on text files", classes="description")
            
            with Horizontal(classes="menu-item"):
                yield Button("Sentence Editor", id="editor", variant="success")
                yield Label("Edit and annotate sentences for NER training", classes="description")
            
            with Horizontal(classes="menu-item"):
                yield Button("SpERT Trainer", id="trainer", variant="primary")
                yield Label("Train SpERT models for entity and relation extraction", classes="description")
            
            with Horizontal(classes="menu-item"):
                yield Button("SpERT Predictor", id="predictor", variant="success")
                yield Label("Run predictions using trained SpERT models", classes="description")
            
            with Horizontal(classes="menu-item"):
                yield Button("Entity Search", id="entity", variant="warning")
                yield Label("Search and explore entities in prediction files", classes="description")

    def on_mount(self) -> None:
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "entity":
            self.push_screen(EntitySearchScreen())
        elif event.button.id == "editor":
            self.push_screen(NEREditorScreen())
        elif event.button.id == "executor":
            self.push_screen(ScriptExecutorScreen())
        elif event.button.id == "preprocessor":
            self.push_screen(TextPreprocessorScreen())
        elif event.button.id == "trainer":
            self.push_screen(SpertTrainerScreen())
        elif event.button.id == "predictor":
            self.push_screen(SpertPredictorScreen())

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())

if __name__ == "__main__":
    app = App()
    app.run()