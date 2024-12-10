from app import create_app

# Create the app instance
app = create_app()

# If you're running with a WSGI server like Gunicorn, it will use this app instance to serve the app
if __name__ == "__main__":
    app.run()
