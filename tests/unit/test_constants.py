from src.utils.constants import APP_VERSION, TEXT_FILE_EXTENSIONS


def test_app_version_is_semver():
    parts = APP_VERSION.split(".")
    assert len(parts) == 3, "APP_VERSION must be X.Y.Z"
    assert all(p.isdigit() for p in parts)


def test_text_file_extensions_are_glob_patterns():
    assert all(ext.startswith("*.") for ext in TEXT_FILE_EXTENSIONS)
    assert len(TEXT_FILE_EXTENSIONS) >= 10  # reasonable minimum
