def generate_local_schema(
    business_name: str,
    location: str,
    website: str | None = None,
    services: list | None = None,
    page_content: dict | None = None,
    business_research: dict | None = None
):
    """
    Generate JSON-LD structured data for a local business page.

    Only uses information actually available from the input.
    """

    services = services or []
    page_content = page_content or {}
    business_research = business_research or {}

    seo = page_content.get("seo", {})

    description = (
        seo.get("meta_description")
        or business_research.get("description")
        or ""
    )

    # --------------------------------
    # LOCAL BUSINESS SCHEMA
    # --------------------------------

    local_business = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": business_name,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": location.split(",")[0].strip()
        }
    }

    # Website only if available
    if website:
        local_business["url"] = website

    # Description only if available
    if description:
        local_business["description"] = description

    # Services only if actually provided
    if services:
        local_business["makesOffer"] = [
            {
                "@type": "Offer",
                "itemOffered": {
                    "@type": "Service",
                    "name": service
                }
            }
            for service in services
            if service
        ]

    # --------------------------------
    # FAQ SCHEMA
    # --------------------------------

    faqs = page_content.get("faqs", [])

    faq_entities = []

    for faq in faqs:
        question = faq.get("question", "").strip()
        answer = faq.get("answer", "").strip()

        if not question or not answer:
            continue

        faq_entities.append({
            "@type": "Question",
            "name": question,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": answer
            }
        })

    faq_schema = None

    if faq_entities:
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_entities
        }

    # --------------------------------
    # FINAL SCHEMA
    # --------------------------------

    schema = {
        "local_business": local_business
    }

    if faq_schema:
        schema["faq_page"] = faq_schema

    return schema