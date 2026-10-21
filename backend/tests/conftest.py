"""Test configuration for running pytest from the repository root."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient

from main import app
from services.review_store import clear_reviews


@pytest.fixture(autouse=True)
def clean_review_store():
    clear_reviews()
    yield
    clear_reviews()


@pytest.fixture
def client():
    return TestClient(app)
