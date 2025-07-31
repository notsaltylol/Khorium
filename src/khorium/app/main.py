from .app import MyTrameApp


def main(server=None, **kwargs):
    app = MyTrameApp(server)
    
    # Configure server for CORS and iframe support
    default_kwargs = {
        "host": "0.0.0.0",
        "cors": True,
    }
    default_kwargs.update(kwargs)
    
    # Print startup message for launcher detection
    print("Starting server...")
    print(f">>> ENGINE: Starting trame server with CORS enabled on {default_kwargs.get('host', '0.0.0.0')}:{default_kwargs.get('port', 10000)}")
    app.server.start(**default_kwargs)


if __name__ == "__main__":
    main()
