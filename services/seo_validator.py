
import re
from collections import Counter


def extract_keywords(keywords):
    """Extract unique keyword phrases from dict or list input."""
    selected = []

    if isinstance(keywords, dict):
        for key in (
            "primary",
            "local_services",
            "commercial_intent",
            "brand",
        ):
            value = keywords.get(key, [])

            if isinstance(value, str):
                selected.append(value)
            elif isinstance(value, list):
                selected.extend(value)

    elif isinstance(keywords, list):
        selected = keywords

    cleaned = []
    seen = set()

    for keyword in selected:
        if not isinstance(keyword, str):
            continue

        keyword = keyword.strip()
        normalized = keyword.casefold()

        if keyword and normalized not in seen:
            cleaned.append(keyword)
            seen.add(normalized)

    return cleaned


def json_safe_text(data):
    """Convert nested content safely into searchable text."""
    if isinstance(data, dict):
        return " ".join(json_safe_text(v) for v in data.values())

    if isinstance(data, (list, tuple)):
        return " ".join(json_safe_text(v) for v in data)

    if data is None:
        return ""

    if isinstance(data, (str, int, float, bool)):
        return str(data)

    return ""


def validate_page(page_content, keywords, location=""):
    """
    Validate generated page content using a fixed 100-point rubric.
    Returns score, checks, keyword_summary and recommendations.
    """
    if not isinstance(page_content, dict):
        page_content = {}

    seo = page_content.get("seo", {})
    if not isinstance(seo, dict):
        seo = {}

    sections = page_content.get("sections", [])
    if not isinstance(sections, list):
        sections = []

    faqs = page_content.get("faqs", [])
    if not isinstance(faqs, list):
        faqs = []

    title = seo.get("title", "")
    description = seo.get("meta_description", "")
    h1 = seo.get("h1", "")

    title = title.strip() if isinstance(title, str) else ""
    description = (
        description.strip()
        if isinstance(description, str)
        else ""
    )
    h1 = h1.strip() if isinstance(h1, str) else ""

    combined_text = json_safe_text({
        "seo": seo,
        "sections": sections,
        "faqs": faqs,
    }).casefold()

    checks = []
    recommendations = []
    score = 0

    def add_check(name, passed, weight, success, failure,
                  details=None, priority="medium"):
        nonlocal score

        checks.append({
            "check": name,
            "status": "passed" if passed else "failed",
            "weight": weight,
            "points_awarded": weight if passed else 0,
            "details": details if details is not None else (
                success if passed else failure
            ),
        })

        if passed:
            score += weight
        else:
            recommendations.append({
                "priority": priority,
                "check": name,
                "message": failure,
                "suggestion": failure,
            })

    # 1. SEO title: 10 points
    add_check(
        "SEO title length",
        30 <= len(title) <= 65,
        10,
        "Title length is within 30–65 characters.",
        (
            f"Write an SEO title of 30–65 characters. "
            f"Current length: {len(title)}."
            if title else "Add a clear SEO title."
        ),
        details=f"Length: {len(title)}",
        priority="high",
    )

    # 2. Meta description: 10 points
    add_check(
        "Meta description length",
        100 <= len(description) <= 170,
        10,
        "Meta description length is within 100–170 characters.",
        (
            f"Adjust the meta description to 100–170 characters. "
            f"Current length: {len(description)}."
            if description else "Add a useful meta description."
        ),
        details=f"Length: {len(description)}",
        priority="high",
    )

    # 3. H1: 10 points
    add_check(
        "H1",
        bool(h1),
        10,
        "H1 is present.",
        "Add one clear, relevant H1 heading.",
        priority="high",
    )

    # 4. Local relevance: 10 points
    location_short = (
        location.split(",")[0].strip().casefold()
        if isinstance(location, str) else ""
    )
    local_found = bool(
        location_short and location_short in combined_text
    )

    add_check(
        "Local relevance",
        local_found,
        10,
        "The target location appears in the generated content.",
        "Include the target city or locality naturally in relevant page content.",
        details=f"Target location: {location_short or 'Not provided'}",
        priority="high",
    )

    # 5. Keyword coverage: 15 points
    actual_keywords = extract_keywords(keywords)
    keywords_to_check = actual_keywords[:10]

    keyword_hits = [
        keyword for keyword in keywords_to_check
        if keyword.casefold() in combined_text
    ]

    keyword_total = len(keywords_to_check)
    keyword_hit_count = len(keyword_hits)

    # Scale the earned points to the number of keywords checked.
    keyword_points = (
        round(15 * keyword_hit_count / keyword_total)
        if keyword_total else 0
    )
    score += keyword_points

    keyword_passed = (
        keyword_total > 0
        and keyword_hit_count / keyword_total >= 0.5
    )

    checks.append({
        "check": "Keyword coverage",
        "status": (
            "passed" if keyword_passed
            else "warning" if keyword_total == 0
            else "failed"
        ),
        "weight": 15,
        "points_awarded": keyword_points,
        "details": (
            f"{keyword_hit_count}/{keyword_total} target keywords found."
            if keyword_total
            else "No target keywords were provided."
        ),
        "keywords_found": keyword_hits,
    })

    if not keyword_passed:
        recommendations.append({
            "priority": "high",
            "check": "Keyword coverage",
            "message": "Target keyword coverage is low or unavailable.",
            "suggestion": (
                "Use relevant service and local-intent keywords naturally "
                "in headings and useful page content. Avoid keyword stuffing."
            ),
        })

    # 6. Content sections: 10 points
    valid_sections = [
        section for section in sections
        if isinstance(section, dict)
    ]

    add_check(
        "Content sections",
        len(valid_sections) >= 5,
        10,
        "At least five structured content sections are present.",
        f"Add useful sections. Current valid section count: {len(valid_sections)}.",
        details=f"Valid sections: {len(valid_sections)}",
        priority="medium",
    )

    # 7. FAQs: 10 points
    valid_faqs = [
        faq for faq in faqs
        if isinstance(faq, dict)
        and isinstance(faq.get("question"), str)
        and faq["question"].strip()
        and isinstance(faq.get("answer"), str)
        and faq["answer"].strip()
    ]

    add_check(
        "FAQ coverage",
        len(valid_faqs) >= 5,
        10,
        "At least five FAQs have a question and answer.",
        f"Add useful FAQs with answers. Current valid FAQ count: {len(valid_faqs)}.",
        details=f"Valid FAQs: {len(valid_faqs)}",
        priority="medium",
    )

    # 8. Content quality: 10 points
    quality_result = validate_content_quality(page_content)
    quality_checks = quality_result["checks"]

    failed_quality = sum(
        1 for item in quality_checks
        if item["status"] == "failed"
    )
    warning_quality = sum(
        1 for item in quality_checks
        if item["status"] == "warning"
    )

    # Grammar and duplicate FAQs are the two hard quality checks.
    quality_points = max(
        0,
        10 - min(10, failed_quality * 5 + warning_quality * 2),
    )
    score += quality_points

    checks.append({
        "check": "Content quality",
        "status": (
            "passed" if failed_quality == 0 and warning_quality == 0
            else "warning" if failed_quality == 0
            else "failed"
        ),
        "weight": 10,
        "points_awarded": quality_points,
        "details": quality_result["issues"],
    })

    for issue in quality_result["issues"]:
        recommendations.append({
            "priority": "medium",
            "check": issue["issue"],
            "message": "Review this content-quality issue.",
            "suggestion": str(issue["details"]),
        })

    # 9. Promotional claims: 5 points
    promotional_claims = [
        "best",
        "#1",
        "number one",
        "leading",
        "top-rated",
        "award-winning",
        "industry-leading",
        "most reliable",
    ]

    found_claims = [
        claim for claim in promotional_claims
        if re.search(
            r"(?<!\w)" + re.escape(claim) + r"(?!\w)",
            combined_text,
        )
    ]

    # Flag claims for human review; presence alone does not prove they are false.
    add_check(
        "Promotional claim review",
        not found_claims,
        5,
        "No flagged promotional phrases were detected.",
        "Review promotional claims and remove or substantiate unsupported wording.",
        details=found_claims,
        priority="medium",
    )

    # 10. Placeholder URLs: 5 points
    placeholder_found = "example.com" in combined_text

    add_check(
        "Placeholder URLs",
        not placeholder_found,
        5,
        "No example.com placeholder was detected.",
        "Replace placeholder URLs with verified URLs or remove them.",
        priority="medium",
    )

    return {
        "score": min(100, max(0, score)),
        "checks": checks,
        "keyword_summary": {
            "total_keywords_checked": keyword_total,
            "keywords_found": keyword_hit_count,
            "matched_keywords": keyword_hits,
        },
        "recommendations": recommendations,
    }


def validate_content_quality(page_content):
    """Detect common grammar, generic-claim and duplicate-FAQ issues."""
    if not isinstance(page_content, dict):
        page_content = {}

    seo = page_content.get("seo", {})
    if not isinstance(seo, dict):
        seo = {}

    sections = page_content.get("sections", [])
    if not isinstance(sections, list):
        sections = []

    faqs = page_content.get("faqs", [])
    if not isinstance(faqs, list):
        faqs = []

    text_parts = []

    for key in ("title", "meta_description", "h1"):
        value = seo.get(key, "")
        if isinstance(value, str):
            text_parts.append(value)

    for section in sections:
        if not isinstance(section, dict):
            continue

        for key in ("heading", "content"):
            value = section.get(key, "")
            if isinstance(value, str):
                text_parts.append(value)

    for faq in faqs:
        if not isinstance(faq, dict):
            continue

        for key in ("question", "answer"):
            value = faq.get(key, "")
            if isinstance(value, str):
                text_parts.append(value)

    normalized_text = re.sub(
        r"\s+", " ", " ".join(text_parts)
    ).strip()
    text_lower = normalized_text.casefold()

    checks = []
    issues = []

    broken_patterns = [
        r"\bteam\s+of\s+s\b",
        r"\bour\s+ise\b",
        r"\ba\s+AI\b",
        r"\bteam\s+of\s+\.\b",
        r"\b(?:is|are)\s+a\s+in\b",
    ]

    broken_matches = [
        pattern for pattern in broken_patterns
        if re.search(pattern, normalized_text, re.IGNORECASE)
    ]

    checks.append({
        "check": "Broken grammar",
        "status": "failed" if broken_matches else "passed",
        "details": broken_matches,
    })

    if broken_matches:
        issues.append({
            "issue": "Possible broken grammar",
            "details": broken_matches,
        })

    generic_claims = [
        "helping them stay ahead",
        "achieve their goals",
        "customer satisfaction",
        "serves businesses in surrounding areas",
        "we occasionally offer discounts",
    ]

    found_generic_claims = [
        phrase for phrase in generic_claims
        if phrase in text_lower
    ]

    checks.append({
        "check": "Generic claim patterns",
        "status": "warning" if found_generic_claims else "passed",
        "details": found_generic_claims,
    })

    if found_generic_claims:
        issues.append({
            "issue": "Potential generic claims",
            "details": found_generic_claims,
        })

    questions = [
        re.sub(r"\s+", " ", faq.get("question", "")).strip().casefold()
        for faq in faqs
        if isinstance(faq, dict)
        and isinstance(faq.get("question"), str)
        and faq["question"].strip()
    ]

    duplicates = sorted(
        question for question, count in Counter(questions).items()
        if count > 1
    )

    checks.append({
        "check": "Duplicate FAQs",
        "status": "failed" if duplicates else "passed",
        "details": duplicates,
    })

    if duplicates:
        issues.append({
            "issue": "Duplicate FAQ questions",
            "details": duplicates,
        })

    return {
        "passed": not issues,
        "checks": checks,
        "issues": issues,
    }
