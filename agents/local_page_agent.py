from datetime import datetime, timezone
import re

from services.business_research import research_business
from services.keyword_research import generate_local_keywords
from services.competitor_analysis import analyze_competitors
from services.page_planner import create_page_plan
from services.page_generator import (
    generate_page_content,
    improve_page_content,
)
from services.seo_validator import validate_page
from services.local_schema import generate_local_schema
from services.html_generator import generate_html

from database.mongo import save_local_page


def create_slug(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


class LocalPageAgent:

    def generate(
        self,
        business_name: str,
        location: str,
        website: str | None,
        services: list
    ):

        # 1. BUSINESS RESEARCH
        business_research = research_business(website)

        # 2. KEYWORD RESEARCH
        keywords = generate_local_keywords(
            business_name=business_name,
            location=location,
            services=services
        )

        # 3. COMPETITOR RESEARCH
        competitors = analyze_competitors(
            business_name=business_name,
            location=location,
            services=services,
            keywords=keywords
        )

        # 4. PAGE PLANNING
        page_plan = create_page_plan(
            business_name=business_name,
            location=location,
            services=services,
            keywords=keywords
        )

        # 5. INITIAL CONTENT GENERATION
        page_content = generate_page_content(
            business_name=business_name,
            location=location,
            services=services,
            keywords=keywords,
            business_research=business_research,
            page_plan=page_plan,
            competitors=competitors
        )

        # 6. INITIAL SEO VALIDATION
        initial_validation = validate_page(
            page_content=page_content,
            keywords=keywords,
            location=location
        )

        initial_score = initial_validation.get("score", 0)
        final_content = page_content
        final_validation = initial_validation
        improvement_applied = False
        improvement_error = None

        # 7. ONE TARGETED SEO IMPROVEMENT ATTEMPT
        recommendations = initial_validation.get(
            "recommendations",
            []
        )

        if recommendations:
            try:
                candidate_content = improve_page_content(
                    page_content=page_content,
                    business_name=business_name,
                    location=location,
                    services=services,
                    keywords=keywords,
                    business_research=business_research,
                    recommendations=recommendations,
                )

                candidate_validation = validate_page(
                    page_content=candidate_content,
                    keywords=keywords,
                    location=location
                )

                candidate_score = candidate_validation.get(
                    "score",
                    0
                )

                # Accept only if the score strictly improves.
                # Otherwise, keep the original generated content.
                if candidate_score > initial_score:
                    final_content = candidate_content
                    final_validation = candidate_validation
                    improvement_applied = True

            except Exception as exc:
                # Keep the original page if improvement fails.
                improvement_error = str(exc)

        page_content = final_content
        seo_validation = final_validation

        # 8. GENERATE SCHEMA FROM FINAL CONTENT
        schema_markup = generate_local_schema(
            business_name=business_name,
            location=location,
            website=website,
            services=services,
            page_content=page_content,
            business_research=business_research
        )

        # 9. GENERATE HTML FROM FINAL CONTENT
        html_content = generate_html(
            business_name=business_name,
            location=location,
            page_content=page_content,
            schema_markup=schema_markup
        )

        # 10. URL SLUG
        location_slug = create_slug(
            location.split(",")[0]
        )
        url_slug = f"/locations/{location_slug}/"

        # 11. SAVE FINAL DOCUMENT
        document = {
            "business_name": business_name,
            "location": location,
            "website": website,
            "services": services,
            "url_slug": url_slug,

            "research": business_research,
            "keywords": keywords,
            "competitors": competitors,
            "page_plan": page_plan,

            "content": page_content,
            "seo_validation": seo_validation,

            "seo_improvement": {
                "attempted": bool(recommendations),
                "applied": improvement_applied,
                "initial_score": initial_score,
                "final_score": seo_validation.get("score", 0),
                "error": improvement_error,
            },

            "schema_markup": schema_markup,
            "html_content": html_content,
            "status": "generated",
            "created_at": datetime.now(timezone.utc)
        }

        page_id = save_local_page(document)

        # 12. API RESPONSE
        return {
            "status": "success",
            "page_id": page_id,

            "business_name": business_name,
            "location": location,
            "url_slug": url_slug,

            "keywords": keywords,

            "competitor_research": {
                "status": competitors.get("status", ""),
                "research_summary": competitors.get(
                    "research_summary",
                    {}
                )
            },

            "competitors": competitors.get(
                "competitors",
                []
            ),

            "seo": page_content.get("seo", {}),
            "sections": page_content.get("sections", []),
            "faqs": page_content.get("faqs", []),

            "schema_markup": schema_markup,
            "html_content": html_content,

            "seo_score": seo_validation.get("score", 0),
            "initial_seo_score": initial_score,

            "seo_improvement": {
                "attempted": bool(recommendations),
                "applied": improvement_applied,
                "initial_score": initial_score,
                "final_score": seo_validation.get("score", 0),
                "error": improvement_error,
            },

            "seo_checks": seo_validation.get("checks", []),
            "seo_recommendations": seo_validation.get(
                "recommendations",
                []
            )
        }
