from typing import List


def generate_local_keywords(
    business_name: str,
    location: str,
    services: List[str]
):
    location_short = location.split(",")[0].strip()

    brand_keywords = [
        business_name,
        f"{business_name} {location_short}",
        f"{business_name} in {location_short}",
        f"{business_name} {location_short} reviews"
    ]

    local_service_keywords = []

    for service in services:
        service = service.strip()

        if not service:
            continue

        local_service_keywords.extend([
            f"{service} in {location_short}",
            f"{service} company in {location_short}",
            f"{service} services in {location_short}"
        ])

    commercial_keywords = []

    for service in services:
        service = service.strip()

        if not service:
            continue

        commercial_keywords.extend([
            f"best {service} in {location_short}",
            f"{service} provider in {location_short}"
        ])

    all_keywords = list(
        dict.fromkeys(
            brand_keywords
            + local_service_keywords
            + commercial_keywords
        )
    )

    return {
        "primary": (
            local_service_keywords[:1]
            if local_service_keywords
            else [
                f"{business_name} in {location_short}"
            ]
        ),
        "brand": brand_keywords,
        "local_services": local_service_keywords,
        "commercial_intent": commercial_keywords,
        "all_keywords": all_keywords
    }