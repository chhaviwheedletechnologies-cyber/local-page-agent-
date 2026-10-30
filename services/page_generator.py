import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:3b"
)


def call_ollama(prompt: str):

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": True,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_predict": 1400
            }
        },
        stream=True,
        timeout=(10, 600)
    )

    response.raise_for_status()

    chunks = []

    for line in response.iter_lines():

        if not line:
            continue

        data = json.loads(
            line.decode("utf-8")
        )

        chunk = data.get(
            "response",
            ""
        )

        if chunk:
            chunks.append(chunk)

        if data.get("done"):
            break

    return "".join(chunks)


def extract_json(raw_response: str):

    if not raw_response:
        raise ValueError(
            "Ollama returned empty response"
        )

    raw_response = raw_response.strip()

    # Remove markdown fences
    if raw_response.startswith("```"):

        raw_response = raw_response.replace(
            "```json",
            ""
        )

        raw_response = raw_response.replace(
            "```",
            ""
        )

        raw_response = raw_response.strip()

    start = raw_response.find("{")
    end = raw_response.rfind("}")

    if start == -1 or end == -1:

        raise ValueError(
            "No JSON object found in Ollama response"
        )

    json_text = raw_response[
        start:end + 1
    ]

    return json.loads(
        json_text
    )


def normalize_keywords(keywords):

    if isinstance(keywords, dict):

        groups = {
            "primary": keywords.get(
                "primary",
                []
            ),
            "brand": keywords.get(
                "brand",
                []
            ),
            "local_services": keywords.get(
                "local_services",
                []
            ),
            "commercial_intent": keywords.get(
                "commercial_intent",
                []
            )
        }

        all_keywords = []

        for values in groups.values():

            for keyword in values:

                if keyword not in all_keywords:
                    all_keywords.append(
                        keyword
                    )

        return groups, all_keywords

    keyword_list = list(
        dict.fromkeys(
            keywords or []
        )
    )

    return {
        "all_keywords": keyword_list
    }, keyword_list


def build_competitor_context(competitors):

    output = []

    for competitor in (
        competitors.get(
            "competitors",
            []
        )[:3]
    ):

        page = competitor.get(
            "page_analysis",
            {}
        )

        output.append({

            "domain": competitor.get(
                "domain",
                ""
            ),

            "title": competitor.get(
                "title",
                ""
            ),

            "h1": page.get(
                "h1",
                []
            )[:3],

            "h2": page.get(
                "h2",
                []
            )[:8],

            "h3": page.get(
                "h3",
                []
            )[:8],

            "faq_sections": page.get(
                "faq_sections",
                []
            )[:5]
        })

    return output



def sanitize_promotional_claims(text: str):
    if not text:
        return ""

    import re

    cleaned = str(text)

    # Remove complete promotional phrases only.
    blocked_phrases = [
        "industry-leading",
        "industry leading",
        "award-winning",
        "award winning",
        "world-class",
        "world class",
        "top-rated",
        "top rated",
        "number one",
        "#1",
        "leading",
        "best",
        "premier",
        "trusted",
    ]

    for phrase in blocked_phrases:
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        cleaned = re.sub(
            pattern, "", cleaned, flags=re.IGNORECASE
        )

    # Fix common grammar issues without damaging valid words.
    cleaned = re.sub(
        r"\b(a)\s+(AI(?:-powered|-based)?)\b",
        r"an \2",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove empty team references created by phrase removal.
    cleaned = re.sub(
        r"\bteam\s+of\s*(?=[,.;:!?]|$)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Normalize whitespace and punctuation.
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"([,;:])\s*([,;:])+", r"\1", cleaned)
    cleaned = re.sub(r"^\s*[,;:]\s*", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)

    return cleaned.strip()


def sanitize_page_result(result: dict):

    if not isinstance(
        result,
        dict
    ):
        return result

    # -------------------------
    # SEO SANITIZATION
    # -------------------------

    seo = result.get(
        "seo",
        {}
    )

    if not isinstance(
        seo,
        dict
    ):
        seo = {}

    result["seo"] = {

        "title": sanitize_promotional_claims(
            str(
                seo.get(
                    "title",
                    ""
                )
            ).strip()
        ),

        "meta_description": sanitize_promotional_claims(
            str(
                seo.get(
                    "meta_description",
                    ""
                )
            ).strip()
        ),

        "h1": sanitize_promotional_claims(
            str(
                seo.get(
                    "h1",
                    ""
                )
            ).strip()
        )
    }

    # -------------------------
    # SECTION SANITIZATION
    # -------------------------

    sections = result.get(
        "sections",
        []
    )

    cleaned_sections = []

    for section in sections:

        if not isinstance(
            section,
            dict
        ):
            continue

        cleaned_sections.append({

            "type": str(
                section.get(
                    "type",
                    ""
                )
            ).strip(),

            "heading": sanitize_promotional_claims(
                str(
                    section.get(
                        "heading",
                        ""
                    )
                ).strip()
            ),

            "content": sanitize_promotional_claims(
                str(
                    section.get(
                        "content",
                        ""
                    )
                ).strip()
            )
        })

    result["sections"] = cleaned_sections

    # -------------------------
    # FAQ SANITIZATION
    # -------------------------

    faqs = result.get(
        "faqs",
        []
    )

    cleaned_faqs = []

    for faq in faqs:

        if not isinstance(
            faq,
            dict
        ):
            continue

        question = sanitize_promotional_claims(
            str(
                faq.get(
                    "question",
                    ""
                )
            ).strip()
        )

        answer = sanitize_promotional_claims(
            str(
                faq.get(
                    "answer",
                    ""
                )
            ).strip()
        )

        if question and answer:

            cleaned_faqs.append({

                "question": question,

                "answer": answer
            })

    result["faqs"] = cleaned_faqs

    return result


def generate_page_content(
    business_name: str,
    location: str,
    services: list,
    keywords,
    business_research: dict,
    page_plan: dict,
    competitors: dict
):

    keyword_groups, all_keywords = (
        normalize_keywords(
            keywords
        )
    )

    # Keep prompt manageable for local 3B model
    selected_keywords = all_keywords[:12]

    business_text = (
        business_research
        .get(
            "text",
            ""
        )
        .strip()
    )

    business_text = business_text[:2500]

    competitor_context = (
        build_competitor_context(
            competitors
        )
    )

    prompt = f"""
Create a local SEO landing page for the business below.

Business:
{business_name}

Location:
{location}

Services:
{json.dumps(
    services,
    ensure_ascii=False
)}

Keyword groups:
{json.dumps(
    keyword_groups,
    ensure_ascii=False
)}

Target keywords:
{json.dumps(
    selected_keywords,
    ensure_ascii=False
)}

Verified business information:
{business_text}

Competitor research:
{json.dumps(
    competitor_context,
    ensure_ascii=False
)}

CONTENT OBJECTIVE:

Create useful, natural and locally relevant page content.
The page should help a user understand what the business
offers in the specified location.

FACTUAL ACCURACY RULES:

1. Use only business facts supported by the
   Verified business information.

2. The following input values are also verified:
   - Business name: {business_name}
   - Location: {location}
   - Services: {json.dumps(services, ensure_ascii=False)}

3. Do not invent:
   - phone numbers
   - addresses
   - email addresses
   - ratings
   - reviews
   - awards
   - certifications
   - clients
   - pricing
   - discounts
   - statistics
   - years of experience
   - team size
   - guarantees
   - offices
   - partnerships
   - delivery timelines
   - business results

4. Do not claim the business is:
   - best
   - leading
   - top
   - top-rated
   - #1
   - number one
   - expert
   - premier
   - trusted
   - award-winning
   - industry-leading
   - world-class

5. Do not create benefits or business advantages
   unless they are explicitly supported by the
   verified information.

6. If information is unavailable, use neutral wording.
   Do not fill the missing information with assumptions.

7. Never turn a keyword into a factual claim.


8. Do not write generic claims such as:
   - "helping businesses stay ahead"
   - "achieve their goals"
   - "customer satisfaction"
   - "reliable and personalized solutions"
   unless the verified business information explicitly supports them.

9. Do not invent business policies or offers.
   Never create FAQs about discounts, promotions, refunds,
   free consultations, pricing, availability, or guarantees
   unless the verified business information explicitly confirms them.

10. FAQ QUALITY:
    - Write exactly 5 useful FAQs relevant to the actual services
      and supplied location.
    - Each question must address a distinct user intent.
    - Answers must use only verified business information.
    - Avoid repeating the same service list in every answer.
    - If a specific detail is unknown, answer honestly without
      inventing it.
    - Do not use questions that assume an unverified business
      feature or policy.

11. WRITING QUALITY:
    - Use grammatically correct, natural English.
    - Never output incomplete phrases such as "team of s"
      or "our ise".
    - Do not leave awkward articles or punctuation after removing
      promotional wording.
    - Do not repeat location keywords unnaturally.
    - Do not claim the business serves nearby areas unless verified.

12. CONTENT EVIDENCE:
    - Competitor content is for topic research only.
    - Never copy competitor claims or present competitor facts
      as facts about this business.
    - Do not infer business capabilities from keywords alone.

KEYWORD RULES:

8. The primary keyword is:
   {json.dumps(
       keyword_groups.get("primary", []),
       ensure_ascii=False
   )}

9. Use the primary keyword naturally in:
   - SEO title
   - H1
   - at least one major section
   - at least one FAQ when natural

10. Use relevant local-service keywords naturally
    throughout the page.

11. Prefer exact local-service keywords when they
    fit naturally.

12. Do not force every keyword into the page.

13. Do not use keyword stuffing.

14. Commercial-intent keywords containing words such
    as "best" are search-intent signals only.
    Do NOT write unsupported claims such as:
    "We are the best AI development company."

15. You may use natural factual alternatives such as:
    "AI Development services in Noida"
    "AI Development company in Noida"
    when supported by the supplied services.

16. Aim to naturally cover multiple relevant
    local-service keywords across the sections,
    especially:
    - AI Development
    - AI Automation
    - Software Development
    - Web Development
    together with the location.

COMPETITOR RULES:

17. Competitor research is only for understanding
    topics, headings and content opportunities.

18. Never mention competitor names.

19. Never copy competitor wording.

20. Never present competitor information as facts
    about the business.

CONTENT QUALITY RULES:

21. Keep sentences grammatically correct.

22. Do not remove a word from a sentence if doing so
    would make the sentence grammatically incorrect.

23. Avoid generic filler.

24. Do not repeat the same sentence across sections.

25. Keep content concise and useful.

26. The "why_choose_us" section must not invent
    advantages. If verified differentiators are
    unavailable, write a neutral explanation of
    the services and business focus instead.

27. The local_information section may state only
    the supplied location. Do not invent local
    offices, service areas or geographic coverage.

28. CTA content should be a neutral invitation to
    learn more or contact the business. Do not
    promise results.

FAQ RULES:

29. Generate exactly 5 FAQs.

30. FAQs should be relevant to the services,
    location and user search intent.

31. Generic educational answers are allowed.

32. Business-specific FAQ answers must use only
    verified information.

33. Do not claim pricing, guarantees, experience,
    results or advantages that were not verified.

OUTPUT RULES:

34. Generate exactly 6 sections.

35. The six section types must be:

hero
about
services
why_choose_us
local_information
cta

36. Return JSON only.

37. No markdown.

38. No explanation outside JSON.

Return exactly:

{{
  "seo": {{
    "title": "",
    "meta_description": "",
    "h1": ""
  }},

  "sections": [
    {{
      "type": "hero",
      "heading": "",
      "content": ""
    }},
    {{
      "type": "about",
      "heading": "",
      "content": ""
    }},
    {{
      "type": "services",
      "heading": "",
      "content": ""
    }},
    {{
      "type": "why_choose_us",
      "heading": "",
      "content": ""
    }},
    {{
      "type": "local_information",
      "heading": "",
      "content": ""
    }},
    {{
      "type": "cta",
      "heading": "",
      "content": ""
    }}
  ],

  "faqs": [
    {{
      "question": "",
      "answer": ""
    }},
    {{
      "question": "",
      "answer": ""
    }},
    {{
      "question": "",
      "answer": ""
    }},
    {{
      "question": "",
      "answer": ""
    }},
    {{
      "question": "",
      "answer": ""
    }}
  ]
}}
"""

    raw_response = call_ollama(
        prompt
    )

    result = extract_json(
        raw_response
    )

    if not isinstance(
        result,
        dict
    ):
        raise ValueError(
            "AI response is not a JSON object"
        )

    # -------------------------
    # SANITIZE AI OUTPUT
    # -------------------------

    result = sanitize_page_result(
        result
    )

    seo = result.get(
        "seo",
        {}
    )

    sections = result.get(
        "sections",
        []
    )

    faqs = result.get(
        "faqs",
        []
    )

    # -------------------------
    # SEO NORMALIZATION
    # -------------------------

    result["seo"] = {

        "title": sanitize_promotional_claims(
            str(
                seo.get(
                    "title",
                    ""
                )
            ).strip()
        ),

        "meta_description": sanitize_promotional_claims(
            str(
                seo.get(
                    "meta_description",
                    ""
                )
            ).strip()
        ),

        "h1": sanitize_promotional_claims(
            str(
                seo.get(
                    "h1",
                    ""
                )
            ).strip()
        )
    }

    # -------------------------
    # SECTION NORMALIZATION
    # -------------------------

    cleaned_sections = []

    allowed_types = {
        "hero",
        "about",
        "services",
        "why_choose_us",
        "local_information",
        "cta"
    }

    for section in sections:

        if not isinstance(
            section,
            dict
        ):
            continue

        section_type = str(
            section.get(
                "type",
                ""
            )
        ).strip()

        if section_type not in allowed_types:
            continue

        cleaned_sections.append({

            "type": section_type,

            "heading": sanitize_promotional_claims(
                str(
                    section.get(
                        "heading",
                        ""
                    )
                ).strip()
            ),

            "content": sanitize_promotional_claims(
                str(
                    section.get(
                        "content",
                        ""
                    )
                ).strip()
            )
        })

    result["sections"] = (
        cleaned_sections[:6]
    )

    # -------------------------
    # FAQ NORMALIZATION
    # -------------------------

    cleaned_faqs = []

    for faq in faqs:

        if not isinstance(
            faq,
            dict
        ):
            continue

        question = sanitize_promotional_claims(
            str(
                faq.get(
                    "question",
                    ""
                )
            ).strip()
        )

        answer = sanitize_promotional_claims(
            str(
                faq.get(
                    "answer",
                    ""
                )
            ).strip()
        )

        if question and answer:

            cleaned_faqs.append({

                "question": question,

                "answer": answer
            })

    result["faqs"] = (
        cleaned_faqs[:5]
    )

    # -------------------------
    # BASIC VALIDATION
    # -------------------------

    if len(result["sections"]) < 6:

        raise ValueError(
            "AI generated fewer than 6 sections"
        )

    if len(result["faqs"]) < 5:

        raise ValueError(
            "AI generated fewer than 5 FAQs"
        )

    return result


def improve_page_content(
    page_content: dict,
    business_name: str,
    location: str,
    services: list,
    keywords,
    business_research: dict,
    recommendations: list,
):
    """
    Make one targeted SEO improvement pass.
    Keeps the same JSON structure and factual-content rules.
    """

    if not isinstance(page_content, dict):
        raise ValueError("page_content must be a dictionary")

    keyword_groups, all_keywords = normalize_keywords(keywords)

    verified_text = business_research.get("text", "")
    if not isinstance(verified_text, str):
        verified_text = ""

    # Keep local-model prompt size manageable.
    verified_text = verified_text[:2000]
    current_content = json.dumps(
        page_content,
        ensure_ascii=False
    )

    current_recommendations = json.dumps(
        recommendations[:8],
        ensure_ascii=False
    )

    prompt = f"""
Improve this existing local SEO page using the validation
recommendations. Return the complete revised page as JSON.

BUSINESS: {business_name}
LOCATION: {location}
VERIFIED SERVICES: {json.dumps(services, ensure_ascii=False)}
KEYWORD GROUPS: {json.dumps(keyword_groups, ensure_ascii=False)}
AVAILABLE VERIFIED BUSINESS INFORMATION:
{verified_text}

CURRENT PAGE JSON:
{current_content}

SEO VALIDATION RECOMMENDATIONS:
{current_recommendations}

RULES:
1. Preserve the JSON structure and keys: seo, sections, faqs.
2. Preserve exactly these six section types, in this order:
   hero, about, services, why_choose_us, local_information, cta.
3. Preserve exactly five FAQs, each with question and answer.
4. Keep seo.title between 30 and 65 characters where possible.
5. Keep seo.meta_description between 100 and 170 characters.
6. Include the primary keyword naturally in the title, H1 and
   relevant page content when grammatically appropriate.
7. Improve keyword coverage naturally. Never stuff keywords.
8. Use the supplied location naturally.
9. Do not invent addresses, phone numbers, emails, ratings,
   reviews, awards, certifications, pricing, guarantees, results,
   experience, clients, team size or business capabilities.
10. Never treat keywords or competitor information as proof of
    a business fact.
11. Remove unsupported promotional claims and generic filler.
12. Keep all factual statements from the current page only when
    supported by the verified information or supplied inputs.
13. Do not add image URLs, HTML, schema or extra JSON keys.
14. If a recommendation cannot be addressed without inventing
    information, leave that part unchanged.
15. Return valid JSON only. No markdown or explanation.

Required JSON structure:
{{
  "seo": {{
    "title": "",
    "meta_description": "",
    "h1": ""
  }},
  "sections": [
    {{"type": "hero", "heading": "", "content": ""}},
    {{"type": "about", "heading": "", "content": ""}},
    {{"type": "services", "heading": "", "content": ""}},
    {{"type": "why_choose_us", "heading": "", "content": ""}},
    {{"type": "local_information", "heading": "", "content": ""}},
    {{"type": "cta", "heading": "", "content": ""}}
  ],
  "faqs": [
    {{"question": "", "answer": ""}},
    {{"question": "", "answer": ""}},
    {{"question": "", "answer": ""}},
    {{"question": "", "answer": ""}},
    {{"question": "", "answer": ""}}
  ]
}}
"""

    raw_response = call_ollama(prompt)
    improved = extract_json(raw_response)

    if not isinstance(improved, dict):
        raise ValueError("Improved content is not a JSON object")

    improved = sanitize_page_result(improved)

    seo = improved.get("seo", {})
    sections = improved.get("sections", [])
    faqs = improved.get("faqs", [])

    required_types = [
        "hero",
        "about",
        "services",
        "why_choose_us",
        "local_information",
        "cta",
    ]

    if not isinstance(seo, dict):
        raise ValueError("Improved SEO data is invalid")

    if not all(
        isinstance(seo.get(key), str) and seo[key].strip()
        for key in ("title", "meta_description", "h1")
    ):
        raise ValueError("Improved SEO fields are incomplete")

    if not isinstance(sections, list) or len(sections) != 6:
        raise ValueError("Improved content must contain six sections")

    if [
        section.get("type")
        for section in sections
        if isinstance(section, dict)
    ] != required_types:
        raise ValueError("Improved section structure is invalid")

    if not all(
        isinstance(section.get("heading"), str)
        and isinstance(section.get("content"), str)
        for section in sections
    ):
        raise ValueError("Improved section fields are invalid")

    if not isinstance(faqs, list) or len(faqs) != 5:
        raise ValueError("Improved content must contain five FAQs")

    if not all(
        isinstance(faq, dict)
        and isinstance(faq.get("question"), str)
        and faq["question"].strip()
        and isinstance(faq.get("answer"), str)
        and faq["answer"].strip()
        for faq in faqs
    ):
        raise ValueError("Improved FAQs are invalid")

    return improved
