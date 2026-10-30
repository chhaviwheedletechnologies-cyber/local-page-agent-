def create_page_plan(
    business_name: str,
    location: str,
    services: list,
    keywords
):

    location_short = (
        location.split(",")[0].strip()
    )

    if isinstance(keywords, dict):

        target_keywords = keywords.get(
            "all_keywords",
            []
        )

    else:

        target_keywords = keywords

    sections = [
        {
            "type": "hero",
            "heading":
                f"{business_name} in {location_short}"
        },
        {
            "type": "about",
            "heading":
                f"About {business_name}"
        },
        {
            "type": "services",
            "heading":
                f"Services in {location_short}"
        },
        {
            "type": "why_choose_us",
            "heading":
                f"Why Choose {business_name}"
        },
        {
            "type": "local_information",
            "heading":
                f"Our {location_short} Location"
        },
        {
            "type": "faq",
            "heading":
                "Frequently Asked Questions"
        },
        {
            "type": "cta",
            "heading":
                "Get Started"
        }
    ]

    return {
        "sections": sections,
        "target_keywords":
            target_keywords
    }