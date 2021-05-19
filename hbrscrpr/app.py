import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from os.path import basename
from pathlib import Path
from typing import Iterator, List, NamedTuple, Optional

import requests
import typer
from bs4 import BeautifulSoup, NavigableString
from tenacity import retry, stop_after_attempt, wait_fixed

article_directory = 'hbrscrpr-articles'
log_format = '%(asctime)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO, datefmt='%H:%M:%S')
habr_url = 'http://habr.com/ru/'

app = typer.Typer()


class Article(NamedTuple):
    name: str
    url: str


@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def save_items(
    path: Path, article_text: Optional[List[str]] = None, img_link: Optional[str] = None
) -> None:
    if article_text:
        with open(path / 'article.txt', 'w+') as file_t:
            file_t.writelines(article_text)
    if img_link:
        img_file = requests.get(img_link).content
        with open(path / 'img' / basename(img_link), 'w+b') as file_b:
            file_b.write(img_file)


def make_directories(directory: Path, article: str) -> Path:
    article_path = directory / article
    Path.mkdir(article_path / 'img', parents=True)
    return article_path


@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def get_articles(amount: int) -> Iterator[Article]:
    r = requests.get(url=habr_url)
    page = 1
    link_counter = 0
    while True:
        soup = BeautifulSoup(r.text, 'html.parser')
        for link in soup.find_all(attrs={'class': 'post__title_link'}):
            if link_counter != amount:
                link_counter += 1
            else:
                return
            logging.info(link)
            yield Article(name=link.text, url=link.get('href'))
        page += 1
        r = requests.get(url=f'http://habr.com/ru/page{page}')


@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def process_article(article: Article, directory: Path) -> None:
    article_path = make_directories(directory, article.name)
    r = requests.get(article.url)
    soup = BeautifulSoup(r.text, 'html.parser')
    post_body = soup.find(attrs={'id': 'post-content-body'})
    article_text = []
    for tag in post_body:
        if isinstance(tag, NavigableString):
            article_text.append(tag.strip('\r'))
        elif re.match(r'(p|pre|code|h[1-6])', tag.name):
            article_text.append(tag.text + '\n')
        elif tag.name == 'img':
            img_link = tag.get('src')
            save_items(path=article_path, img_link=img_link)
    save_items(path=article_path, article_text=article_text)


@app.command()
def main(
    amount: int = typer.Option(default=30, min=0),
    workers: int = typer.Option(default=4, min=1),
    path: str = typer.Option(default=article_directory),
) -> None:
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_list = []
        for article in get_articles(amount):
            future_list.append(executor.submit(process_article, article, Path(path)))
        with typer.progressbar(
            as_completed(future_list), label='Processing pages', length=amount
        ) as progress:
            for _ in progress:
                pass


if __name__ == '__main__':
    logging.info('Started')
    app()
    logging.info('Finished')
