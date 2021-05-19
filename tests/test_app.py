from typer.testing import CliRunner

from hbrscrpr.app import app

runner = CliRunner()


def test_cli_normal(article_directory):
    result = runner.invoke(
        app, ['--amount', '1', '--workers', '8', '--path', str(article_directory)]
    )
    assert result.exit_code == 0
    assert len(list(article_directory.iterdir())) == 1


def test_cli_less_than_zero_articles(article_directory):
    result = runner.invoke(
        app, ['--amount', '-5', '--workers', '8', '--path', str(article_directory)]
    )
    assert result.exit_code == 2
    assert (
        "Error: Invalid value for '--amount': -5 is smaller than the minimum valid value 0"
        in result.output
    )


def test_cli_less_than_one_worker(article_directory):
    result = runner.invoke(
        app, ['--amount', '10', '--workers', '0', '--path', str(article_directory)]
    )
    assert result.exit_code == 2
    assert (
        "Error: Invalid value for '--workers': 0 is smaller than the minimum valid value 1"
        in result.output
    )
