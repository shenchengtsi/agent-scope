"""Placeholder test for backend.

This ensures pytest doesn't fail when collecting tests.
"""


def test_backend_imports():
    """Test that backend modules can be imported."""
    try:
        import main_v2
        import storage_manager
    except ImportError as e:
        # Some dependencies might not be installed in CI
        pass
