import sys
from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer, Static, Checkbox, Label, ListView, ListItem

from tasks.models import Task
from tasks import config, storage

from tasks.tui.edit import EditScreen


# TODO: Move get and write tasks to a more centralised location together with cli functions.
def _get_tasks() -> list[Task]:
    conf = config.read_config()
    if conf.storage_type == "json":
        return storage.tasks_from_json(conf.storage_path)
    else:
        NotImplementedError(f"Storage type '{conf.storage_type}' is not supported")


def _write_tasks(tasks: list[Task]) -> None:
    conf = config.read_config()
    if conf.storage_type == "json":
        storage.tasks_to_json(conf.storage_path, tasks)
    else:
        NotImplementedError(f"Storage type '{conf.storage_type}' is not supported")


class TaskWidget(Static):
    def __init__(self, task: Task) -> None:
        super().__init__()
        self.__task = task  # Note: attribute 'task' seems to be already taken

    def compose(self) -> ComposeResult:
        yield Checkbox(value=self.__task.done)
        yield Label(self.__task.name)
    
    def get_task(self) -> Task:
        return self.__task
    
    def set_task(self, task: Task) -> None:
        self.__task = task
        self.refresh(recompose=True)  # TODO: Can we avoid recompose? Reactive params?


class TaskApp(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("n", "new", "New"),
        ("e", "edit", "Edit"),
        ("r", "remove", "Remove"),
        ("c", "config", "Config"),
    ]

    # SCREENS = {"edit_screen": EditScreen}

    CSS_PATH = "taskapp.tcss"

    def compose(self) -> ComposeResult:
        tasks = _get_tasks()
        yield Header()
        yield ListView(*[ListItem(TaskWidget(task)) for task in tasks])
        yield Footer()

    def action_quit(self) -> None:
        # TODO: Should we save here as well?
        sys.exit()

    @work
    async def action_new(self) -> None:
        """Adds a new task and directly opens it for editing"""
        list_view = self.query_one(ListView)
        task_widget = TaskWidget(Task.new(""))
        list_item = ListItem(task_widget)

        # Requires @work and await to make sure that we get results before processing
        await self.push_screen_wait(EditScreen(task_widget.get_task(), task_widget.set_task))

        list_view.append(list_item)
        list_view.index = len(list_view) - 1  # Highlight created
        list_item.scroll_visible()  # FIXME: Scrolls from top every time...

    def action_edit(self) -> None:
        """Opens a new window for editing the selected task"""
        list_view = self.query_one(ListView)
        task_widget = list_view.highlighted_child.query_one(TaskWidget)

        self.push_screen(EditScreen(task_widget.get_task()), task_widget.set_task) # TODO: Send whole task widget?

    def action_remove(self) -> None:
        """Removes the selected task"""
        list_view = self.query_one(ListView)
        idx = list_view.index
        if list_view.highlighted_child:
            list_view.highlighted_child.remove()

        # TODO: Below we try to reactivate highlightning for closest item but doesnt work
        list_view.index = idx if 0 <= idx < len(list_view) else len(list_view) - 1

        # TODO: Removes even if nothing is highlighted...
        # since it doesnt update visuals after removal.

    def action_config(self) -> None:
        """Opens a new window for modifying configurations"""
        raise NotImplementedError()


def main() -> int:
    app = TaskApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
