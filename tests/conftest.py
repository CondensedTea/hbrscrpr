import pytest


@pytest.fixture()
def article_directory(tmp_path):
    d = tmp_path / 'articles'
    d.mkdir()
    return d
