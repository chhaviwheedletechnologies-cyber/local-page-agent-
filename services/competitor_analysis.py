from urllib.parse import urlparse

from services.serp_research import search_serp
from services.competitor_scraper import scrape_competitor_page


EXCLUDED_DOMAINS = {
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "wikipedia.org",
    "quora.com",
    "medium.com",
    "naukri.com",
    "indeed.com",
    "glassdoor.com",
    "ambitionbox.com",
    "crunchbase.com",
    "rocketreach.co",
    "justdial.com",
    "sulekha.com",
    "yelp.com",
    "pinterest.com",
    "tiktok.com",
}


def extract_domain(url: str):
    try:
        domain = urlparse(url).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:
        return ""


def is_excluded_domain(domain: str):

    if not domain:
        return True

    return any(
        domain == excluded
        or domain.endswith("." + excluded)
        for excluded in EXCLUDED_DOMAINS
    )


def normalize(value: str):

    return (
        str(value)
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .replace(".", "")
    )


def is_own_business(
    domain: str,
    business_name: str
):

    business_normalized = normalize(
        business_name
    )

    domain_normalized = normalize(
        domain
    )

    if not business_normalized:
        return False

    # Direct business/domain match
    if business_normalized in domain_normalized:
        return True

    # Compare meaningful business words
    raw_words = (
        str(business_name)
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace(".", " ")
        .split()
    )

    meaningful_words = [
        word
        for word in raw_words
        if len(word) >= 4
    ]

    if len(meaningful_words) >= 2:

        if all(
            normalize(word) in domain_normalized
            for word in meaningful_words
        ):
            return True

    return False


def get_research_keywords(keywords):

    if isinstance(keywords, dict):

        local_keywords = keywords.get(
            "local_services",
            []
        )

        commercial_keywords = keywords.get(
            "commercial_intent",
            []
        )
        
        # Prioritize local service searches first
        research_keywords = (
            local_keywords[:4]
            + commercial_keywords[:2]
        )

    else:

        research_keywords = keywords or []

    return list(
        dict.fromkeys(
            research_keywords
        )
    )[:6]


def analyze_competitors(
    business_name: str,
    location: str,
    services: list,
    keywords
):

    # =====================================================
    # 1. KEYWORDS
    # =====================================================

    research_keywords = get_research_keywords(
        keywords
    )

    competitor_map = {}

    serp_results = []

    serp_summary = {
        "keywords_attempted": len(
            research_keywords
        ),
        "successful_searches": 0,
        "failed_searches": 0,
        "not_configured": 0,
        "organic_results_found": 0,
        "excluded_results": 0,
        "own_business_results": 0,
        "usable_results": 0,
        "errors": []
    }

    # =====================================================
    # 2. SERP SEARCH
    # =====================================================

    for keyword in research_keywords:

        result = search_serp(
            keyword=keyword,
            location=location
        )

        serp_results.append(result)

        status = result.get(
            "status"
        )

        # -------------------------------------------------
        # API NOT CONFIGURED
        # -------------------------------------------------

        if status == "not_configured":

            serp_summary[
                "not_configured"
            ] += 1

            continue

        # -------------------------------------------------
        # SEARCH FAILED
        # -------------------------------------------------

        if status == "rate_limited":

            serp_summary[
                "failed_searches"
            ] += 1
            
            error_message = result.get(
                "error"
            )

            if error_message:

                serp_summary[
                    "errors"
                ].append({
                    "keyword": keyword,
                    "error": error_message
                })
                
            # Stop immediately.
            # There is no reason to send the remaining requests
            # when the provider has already rate-limited us.
            break

        if status != "success":
            serp_summary["failed_searches"] += 1

            error_message = result.get("error")

            if error_message:
                serp_summary["errors"].append({
                    "keyword": keyword,
                    "error": error_message
                })

            continue

        # -------------------------------------------------
        # SEARCH SUCCESS
        # -------------------------------------------------

        serp_summary[
            "successful_searches"
        ] += 1

        organic_results = result.get(
            "results",
            []
        )

        serp_summary[
            "organic_results_found"
        ] += len(
            organic_results
        )

        # =================================================
        # 3. PROCESS ORGANIC RESULTS
        # =================================================

        for item in organic_results:

            url = item.get(
                "link"
            )

            if not url:
                continue

            domain = extract_domain(
                url
            )

            if not domain:
                continue

            # -------------------------------------------------
            # EXCLUDED DOMAIN
            # -------------------------------------------------

            if is_excluded_domain(
                domain
            ):

                serp_summary[
                    "excluded_results"
                ] += 1

                continue

            # -------------------------------------------------
            # OWN BUSINESS
            # -------------------------------------------------

            if is_own_business(
                domain,
                business_name
            ):

                serp_summary[
                    "own_business_results"
                ] += 1

                continue

            # -------------------------------------------------
            # CREATE / MERGE COMPETITOR
            # -------------------------------------------------

            if domain not in competitor_map:

                competitor_map[domain] = {

                    "domain": domain,

                    "title": item.get(
                        "title",
                        ""
                    ),

                    "url": url,

                    "keywords_found": [],

                    "positions": [],

                    "page_analysis": {}
                }

            competitor = (
                competitor_map[domain]
            )

            # -------------------------------------------------
            # KEYWORD VISIBILITY
            # -------------------------------------------------

            if keyword not in (
                competitor[
                    "keywords_found"
                ]
            ):

                competitor[
                    "keywords_found"
                ].append(
                    keyword
                )

            # -------------------------------------------------
            # POSITION
            # -------------------------------------------------

            position = item.get(
                "position"
            )

            if position is not None:

                competitor[
                    "positions"
                ].append(
                    position
                )

    # =====================================================
    # 4. COUNT UNIQUE COMPETITORS
    # =====================================================

    serp_summary[
        "usable_results"
    ] = len(
        competitor_map
    )

    # =====================================================
    # 5. CREATE COMPETITOR LIST
    # =====================================================

    competitors = list(
        competitor_map.values()
    )

    # =====================================================
    # 6. SCORE COMPETITORS
    # =====================================================

    for competitor in competitors:

        positions = competitor.get(
            "positions",
            []
        )

        keywords_found = competitor.get(
            "keywords_found",
            []
        )

        keyword_count = len(
            keywords_found
        )

        if positions:

            average_position = round(
                sum(positions)
                / len(positions),
                2
            )

        else:

            average_position = 999

        competitor[
            "average_position"
        ] = average_position

        competitor[
            "keyword_count"
        ] = keyword_count

        # Higher visibility + better ranking
        # = stronger competitor

        ranking_score = max(
            0,
            20 - average_position
        )

        visibility_score = (
            keyword_count * 10
        )

        competitor[
            "competitor_score"
        ] = round(
            visibility_score
            + ranking_score,
            2
        )

    # =====================================================
    # 7. SORT
    # =====================================================

    competitors.sort(
        key=lambda item: (
            -item.get(
                "competitor_score",
                0
            ),
            item.get(
                "average_position",
                999
            )
        )
    )

    # Keep top 5
    competitors = competitors[:5]

    # =====================================================
    # 8. SCRAPE TOP COMPETITORS
    # =====================================================

    for competitor in competitors:

        competitor[
            "page_analysis"
        ] = scrape_competitor_page(
            competitor["url"]
        )

    # =====================================================
    # 9. STATUS
    # =====================================================

    if (
        serp_summary["not_configured"]
        == len(research_keywords)
        and research_keywords
    ):

        overall_status = (
            "serp_api_not_configured"
        )

    elif (
        serp_summary[
            "successful_searches"
        ] == 0
        and research_keywords
    ):

        overall_status = (
            "serp_search_failed"
        )

    elif (
        serp_summary[
            "successful_searches"
        ] > 0
        and serp_summary[
            "organic_results_found"
        ] == 0
    ):

        overall_status = (
            "no_organic_results"
        )

    elif (
        serp_summary[
            "successful_searches"
        ] > 0
        and len(competitors) == 0
    ):

        overall_status = (
            "no_usable_competitors"
        )

    else:

        overall_status = "success"

    # =====================================================
    # 10. FINAL RESULT
    # =====================================================

    return {

        "status": overall_status,

        "business_name":
            business_name,

        "location":
            location,

        "keywords_analyzed":
            research_keywords,

        "research_summary":
            serp_summary,

        "serp_results":
            serp_results,

        "competitors":
            competitors
    }