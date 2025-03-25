from models import create_app  # Import create_app from models/__init__.py

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
