# --- Textual ---

from textual import work
from textual.reactive import reactive
from textual.widgets import Label

# App lifecycle

app.run()  # start

app.push_screen(SomeScreen())  # navigate

app.pop_screen()  # go back

app.exit()  # quit

# Querying widgets

self.query_one("#my-id", Label)  # by id, typed

self.query_one("GameScreen", GameScreen)  # by type

self.query(ShotGlass)  # all matching

# Reactivity

foo: reactive[int] = reactive(0)  # changing foo triggers render()


def watch_foo(self, new: int): ...  # called when foo changes


# Timers

self.set_timer(2.0, callback)  # fire once after 2s

self.set_interval(0.5, callback)  # fire every 0.5s


# Async background tasks

@work(exclusive=True)
async def my_worker(self): ...  # non-blocking background task


# CSS

self.add_class("my-class")

self.remove_class("my-class")

self.toggle_class("my-class")
