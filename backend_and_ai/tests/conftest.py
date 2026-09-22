import os

# Integration tests need a real Postgres; point the app at it before any app module is imported.
if os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
