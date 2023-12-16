


from pynicotine.events import events


class WebApi:
    def __init__(self):
        for event_name, callback in (
            ("quit", self._quit),
            ("start", self._start)
        ):
            events.connect(event_name, callback)

    def _start(self):
        print("Run the WebAPI")

    def _quit(self):
        print("Stop the WebAPI")
