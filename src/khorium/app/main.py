from .app import MyTrameApp


def main(server=None, **kwargs):
    app = MyTrameApp(server)
    
    # Configure server for CORS and iframe support
    default_kwargs = {
        "port": 10000,
        "host": "0.0.0.0",
        "cors": True,
    }
    default_kwargs.update(kwargs)
    
    print(f">>> ENGINE: Starting trame server with CORS enabled on {default_kwargs['host']}:{default_kwargs['port']}")
    app.server.start(**default_kwargs)


if __name__ == "__main__":
    main()
