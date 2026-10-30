import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def research_business(website: str | None):

    if not website:
        return {
            "title": "",
            "description": "",
            "h1": "",
            "text": "",
            "links": []
        }

    try:

        response = requests.get(
            website,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        title = ""

        if soup.title:
            title = soup.title.get_text(
                strip=True
            )

        description = ""

        meta = soup.find(
            "meta",
            attrs={"name": "description"}
        )

        if meta:
            description = meta.get(
                "content",
                ""
            )

        h1 = ""

        h1_tag = soup.find("h1")

        if h1_tag:
            h1 = h1_tag.get_text(
                " ",
                strip=True
            )

        for tag in soup([
            "script",
            "style",
            "noscript"
        ]):
            tag.decompose()

        text = soup.get_text(
            " ",
            strip=True
        )

        text = text[:10000]

        links = []

        for link in soup.find_all(
            "a",
            href=True
        ):

            href = urljoin(
                website,
                link["href"]
            )

            links.append(href)

        return {
            "title": title,
            "description": description,
            "h1": h1,
            "text": text,
            "links": links[:50]
        }

    except Exception as e:

        return {
            "error": str(e),
            "title": "",
            "description": "",
            "h1": "",
            "text": "",
            "links": []
        }