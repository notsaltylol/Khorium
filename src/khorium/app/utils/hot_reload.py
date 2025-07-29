def setup_hot_reload(server, build_ui_callback):
    """Setup hot reload functionality for development"""
    try:
        import asyncio
        from pathlib import Path

        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        current_event_loop = asyncio.get_event_loop()

        def update_ui():
            with server.state:
                build_ui_callback()

        class UpdateUIOnChange(FileSystemEventHandler):
            def on_modified(self, event):
                current_event_loop.call_soon_threadsafe(update_ui)

        observer = Observer()
        observer.schedule(
            UpdateUIOnChange(),
            str(Path(__file__).parent.absolute()),
            recursive=False,
        )
        observer.start()
    except ImportError:
        print("Watchdog not installed so skipping the auto monitoring")