import requests

from bs4 import BeautifulSoup


def scrape_competitor_page(
    url: str
):

    try:

        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/154.0 Safari/537.36"
                )
            }
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Remove non-content elements.
        for tag in soup([
            "script",
            "style",
            "noscript",
            "svg",
            "iframe",
            "nav",
            "footer"
        ]):

            tag.decompose()

        # -----------------------------------------------------
        # TITLE
        # -----------------------------------------------------

        title = ""

        if soup.title:

            title = soup.title.get_text(
                " ",
                strip=True
            )

        # -----------------------------------------------------
        # META DESCRIPTION
        # -----------------------------------------------------

        meta_description = ""

        meta = soup.find(
            "meta",
            attrs={
                "name": "description"
            }
        )

        if meta:

            meta_description = (
                meta.get(
                    "content",
                    ""
                )
                .strip()
            )

        # -----------------------------------------------------
        # HEADINGS
        # -----------------------------------------------------

        h1 = [
            tag.get_text(
                " ",
                strip=True
            )

            for tag in soup.find_all(
                "h1"
            )

            if tag.get_text(
                " ",
                strip=True
            )
        ]

        h2 = [
            tag.get_text(
                " ",
                strip=True
            )

            for tag in soup.find_all(
                "h2"
            )

            if tag.get_text(
                " ",
                strip=True
            )
        ]

        h3 = [
            tag.get_text(
                " ",
                strip=True
            )

            for tag in soup.find_all(
                "h3"
            )

            if tag.get_text(
                " ",
                strip=True
            )
        ]

        # -----------------------------------------------------
        # FAQ DETECTION
        # -----------------------------------------------------

        faq_sections = []

        for tag in soup.find_all(
            [
                "h2",
                "h3",
                "h4"
            ]
        ):

            heading = tag.get_text(
                " ",
                strip=True
            )

            heading_lower = (
                heading.lower()
            )

            if (
                "faq" in heading_lower
                or
                "frequently asked" in heading_lower
                or
                "questions" in heading_lower
            ):

                faq_sections.append(
                    heading
                )

        # -----------------------------------------------------
        # MAIN CONTENT
        # -----------------------------------------------------

        content = soup.get_text(
            " ",
            strip=True
        )

        content = " ".join(
            content.split()
        )

        content = content[:15000]

        return {

            "status":
                "success",

            "url":
                url,

            "title":
                title,

            "meta_description":
                meta_description,

            "h1":
                h1[:10],

            "h2":
                h2[:30],

            "h3":
                h3[:30],

            "faq_sections":
                faq_sections[:20],

            "content":
                content

        }

    except Exception as e:

        return {

            "status":
                "error",

            "url":
                url,

            "title":
                "",

            "meta_description":
                "",

            "h1":
                [],

            "h2":
                [],

            "h3":
                [],

            "faq_sections":
                [],

            "content":
                "",

            "error":
                str(e)

        }