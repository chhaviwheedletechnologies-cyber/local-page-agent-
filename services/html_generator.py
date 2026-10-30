
import html
import json
import re
from urllib.parse import urlparse


def escape(value):
    """Safely escape text before inserting it into HTML."""
    if value is None:
        return ""

    return html.escape(str(value), quote=True)


def safe_json_for_html(data):
    """Prevent JSON-LD values from accidentally closing the script tag."""
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def make_id(value, fallback="section"):
    """Create a safe HTML element ID."""
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = value.strip("-_")
    return value or fallback


def generate_html(
    business_name: str,
    location: str,
    page_content: dict,
    schema_markup: dict
):
    page_content = page_content if isinstance(page_content, dict) else {}
    schema_markup = schema_markup if isinstance(schema_markup, dict) else {}

    seo = page_content.get("seo") or {}
    seo = seo if isinstance(seo, dict) else {}

    sections = page_content.get("sections") or []
    sections = sections if isinstance(sections, list) else []

    faqs = page_content.get("faqs") or []
    faqs = faqs if isinstance(faqs, list) else []

    business_name = str(business_name or "Local Business").strip()
    location = str(location or "").strip()
    location_short = location.split(",")[0].strip() or location

    # -------------------------------------------------
    # CLEAN AND DEDUPLICATE FAQS
    # -------------------------------------------------

    cleaned_faqs = []
    seen_questions = set()

    for faq in faqs:
        if not isinstance(faq, dict):
            continue

        question = " ".join(str(faq.get("question") or "").split())
        answer = " ".join(str(faq.get("answer") or "").split())

        if not question or not answer:
            continue

        question_key = question.casefold()

        if question_key in seen_questions:
            continue

        seen_questions.add(question_key)
        cleaned_faqs.append({
            "question": question,
            "answer": answer
        })

    # -------------------------------------------------
    # SEO METADATA
    # -------------------------------------------------

    title = seo.get("title") or f"{business_name} in {location_short}"
    meta_description = seo.get("meta_description") or ""
    h1 = seo.get("h1") or f"{business_name} in {location_short}"

    # -------------------------------------------------
    # LOCAL BUSINESS SCHEMA
    # -------------------------------------------------

    local_business_schema = schema_markup.get("local_business")
    if not isinstance(local_business_schema, dict):
        local_business_schema = None

    website_url = ""
    if local_business_schema:
        website_url = str(local_business_schema.get("url") or "").strip()

    parsed_url = urlparse(website_url)
    if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
        website_url = ""

    canonical_url = ""
    if website_url:
        canonical_slug = make_id(location_short, "location")
        canonical_url = (
            f"{website_url.rstrip('/')}/locations/{canonical_slug}/"
        )

    # -------------------------------------------------
    # PREPARE HTML
    # -------------------------------------------------

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>{escape(title)}</title>",
        f'<meta name="description" content="{escape(meta_description)}">',
        '<meta name="robots" content="index, follow">',
        f'<meta property="og:title" content="{escape(title)}">',
        f'<meta property="og:description" content="{escape(meta_description)}">',
        '<meta property="og:type" content="website">'
    ]

    if canonical_url:
        html_parts.append(
            f'<link rel="canonical" href="{escape(canonical_url)}">'
        )

    # Add LocalBusiness JSON-LD only when available.
    if local_business_schema:
        html_parts.append(
            '<script type="application/ld+json">'
            + safe_json_for_html(local_business_schema)
            + "</script>"
        )

    # Add FAQ schema for the FAQs actually displayed on the page.
    if cleaned_faqs:
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": faq["question"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": faq["answer"]
                    }
                }
                for faq in cleaned_faqs
            ]
        }

        html_parts.append(
            '<script type="application/ld+json">'
            + safe_json_for_html(faq_schema)
            + "</script>"
        )

    # -------------------------------------------------
    # CSS
    # -------------------------------------------------

    html_parts.append("""
<style>
* { box-sizing: border-box; }

html { scroll-behavior: smooth; }

body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.6;
    color: #222;
    background: #fff;
}

a { text-decoration: none; }

.container {
    width: 100%;
    max-width: 1150px;
    margin: 0 auto;
    padding: 0 24px;
}

.site-header {
    border-bottom: 1px solid #e5e5e5;
    background: #fff;
}

.navbar {
    min-height: 70px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 30px;
}

.brand {
    font-size: 21px;
    font-weight: 700;
    color: #222;
}

.nav-links {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 20px;
}

.nav-links a {
    color: #444;
    font-size: 15px;
}

.nav-links a:hover { text-decoration: underline; }

.hero {
    padding: 90px 20px;
    text-align: center;
    background: #f5f7fa;
}

.hero h1 {
    max-width: 850px;
    margin: 0 auto 20px;
    font-size: 46px;
    line-height: 1.15;
}

.hero-location {
    margin: 0 auto 28px;
    font-size: 18px;
    color: #555;
}

.hero-button, .cta-button {
    display: inline-block;
    padding: 13px 24px;
    border-radius: 6px;
    background: #222;
    color: #fff;
    font-weight: 600;
}

.section { padding: 70px 0; }

.section h2 {
    margin: 0 0 20px;
    font-size: 32px;
    line-height: 1.25;
}

.section-content {
    max-width: 900px;
    font-size: 18px;
    color: #444;
    overflow-wrap: anywhere;
}

.services-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
    margin-top: 30px;
}

.service-card {
    padding: 25px;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    background: #fff;
}

.service-card h3 { margin-top: 0; }

.faq-section {
    padding: 70px 0;
    background: #fff;
}

.faq-item {
    max-width: 900px;
    padding: 22px 0;
    border-bottom: 1px solid #e5e5e5;
}

.faq-item h3 {
    margin: 0 0 10px;
    font-size: 20px;
}

.faq-item p { margin: 0; color: #555; }

.cta {
    padding: 80px 20px;
    text-align: center;
    background: #f5f7fa;
}

.cta h2 { margin-bottom: 15px; font-size: 34px; }

.cta-content {
    max-width: 750px;
    margin: 0 auto 25px;
    font-size: 18px;
    color: #555;
}

.contact-form {
    max-width: 700px;
    margin: 30px auto 0;
    display: grid;
    gap: 16px;
    text-align: left;
}

.contact-form label {
    display: block;
    margin-bottom: 6px;
    font-weight: 600;
    color: #333;
}

.contact-form input, .contact-form textarea {
    width: 100%;
    padding: 12px 14px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font: inherit;
    background: #fff;
}

.contact-form button {
    padding: 14px 22px;
    border: 0;
    border-radius: 6px;
    background: #222;
    color: #fff;
    font: inherit;
    font-weight: 600;
    cursor: pointer;
}

.contact-form button:disabled {
    opacity: 0.6;
    cursor: wait;
}

#contact-status {
    margin-top: 12px;
    font-weight: 600;
    overflow-wrap: anywhere;
}

.site-footer {
    padding: 35px 0;
    border-top: 1px solid #e5e5e5;
    background: #fff;
}

.footer-content {
    text-align: center;
    color: #666;
    font-size: 14px;
}

@media (max-width: 768px) {
    .navbar {
        padding: 15px 0;
        flex-direction: column;
        align-items: flex-start;
    }

    .hero { padding: 65px 20px; }
    .hero h1 { font-size: 34px; }
    .section { padding: 50px 0; }
    .section h2 { font-size: 28px; }
}
</style>
""")

    html_parts.append("</head>")
    html_parts.append("<body>")

    # -------------------------------------------------
    # NAVIGATION
    # -------------------------------------------------

    html_parts.append(f"""
<header class="site-header">
    <div class="container">
        <nav class="navbar">
            <a class="brand" href="#top">{escape(business_name)}</a>
            <div class="nav-links">
                <a href="#about">About</a>
                <a href="#services">Services</a>
                <a href="#location">Location</a>
                <a href="#faq">FAQ</a>
                <a href="#contact">Contact</a>
            </div>
        </nav>
    </div>
</header>
""")

    # -------------------------------------------------
    # MAIN AND HERO
    # -------------------------------------------------

    html_parts.append("<main>")

    html_parts.append(f"""
<section class="hero" id="top">
    <div class="container">
        <h1>{escape(h1)}</h1>
        <p class="hero-location">{escape(location)}</p>
        <a class="hero-button" href="#contact">Get Started</a>
    </div>
</section>
""")

    # -------------------------------------------------
    # CONTENT SECTIONS
    # -------------------------------------------------

    contact_rendered = False
    used_ids = {"top", "faq", "contact"}

    id_mapping = {
        "about": "about",
        "services": "services",
        "local_information": "location",
        "why_choose_us": "why-choose-us"
    }

    for section in sections:
        if not isinstance(section, dict):
            continue

        section_type = str(section.get("type") or "section").strip().lower()
        heading = section.get("heading") or ""
        content = section.get("content") or ""

        if section_type in ("hero", "faq"):
            continue

        # Render one contact form when a CTA section is found.
        if section_type == "cta":
            if contact_rendered:
                continue

            contact_rendered = True

            html_parts.append('<section class="cta" id="contact">')
            html_parts.append('<div class="container">')
            html_parts.append(
                f"<h2>{escape(heading or 'Get in Touch')}</h2>"
            )

            if content:
                html_parts.append(
                    f'<div class="cta-content">{escape(content)}</div>'
                )

            html_parts.append("""
<form class="contact-form" id="contact-form">
    <div>
        <label for="contact-name">Name</label>
        <input id="contact-name" name="name"
               type="text" maxlength="100" autocomplete="name" required>
    </div>
    <div>
        <label for="contact-email">Email</label>
        <input id="contact-email" name="email"
               type="email" maxlength="254" autocomplete="email" required>
    </div>
    <div>
        <label for="contact-message">Message</label>
        <textarea id="contact-message" name="message"
                  rows="5" maxlength="5000" required></textarea>
    </div>
    <button type="submit">Send Message</button>
    <p id="contact-status" role="status" aria-live="polite"></p>
</form>
""")

            html_parts.append("</div></section>")
            continue

        section_id = id_mapping.get(
            section_type,
            make_id(section_type)
        )

        # Avoid duplicate IDs that could break navigation.
        if section_id in used_ids:
            section_id = make_id(f"{section_id}-{len(used_ids)}")

        used_ids.add(section_id)

        html_parts.append(
            f'<section class="section" id="{escape(section_id)}">'
        )
        html_parts.append('<div class="container">')

        if heading:
            html_parts.append(f"<h2>{escape(heading)}</h2>")

        if content:
            html_parts.append(
                f'<div class="section-content">{escape(content)}</div>'
            )

        # Render service cards when structured offers are available.
        if section_type == "services" and local_business_schema:
            offers = local_business_schema.get("makesOffer", [])
            service_names = []

            if isinstance(offers, list):
                for offer in offers:
                    if not isinstance(offer, dict):
                        continue

                    item = offer.get("itemOffered", {})
                    if not isinstance(item, dict):
                        continue

                    service_name = item.get("name")
                    if service_name and str(service_name).strip():
                        service_names.append(str(service_name).strip())

            if service_names:
                html_parts.append('<div class="services-grid">')

                for service_name in dict.fromkeys(service_names):
                    html_parts.append(
                        f'<div class="service-card">'
                        f'<h3>{escape(service_name)}</h3>'
                        f'<p>{escape(service_name)} services'
                        f' in {escape(location_short)}.</p>'
                        f'</div>'
                    )

                html_parts.append("</div>")

        html_parts.append("</div></section>")

    # -------------------------------------------------
    # ALWAYS RENDER CONTACT FORM
    # -------------------------------------------------

    # The navigation and hero CTA must work even if the AI did not
    # generate a section with type="cta".
    if not contact_rendered:
        html_parts.append("""
<section class="cta" id="contact">
    <div class="container">
        <h2>Contact Us</h2>
        <form class="contact-form" id="contact-form">
            <div>
                <label for="contact-name">Name</label>
                <input id="contact-name" name="name"
                       type="text" maxlength="100"
                       autocomplete="name" required>
            </div>
            <div>
                <label for="contact-email">Email</label>
                <input id="contact-email" name="email"
                       type="email" maxlength="254"
                       autocomplete="email" required>
            </div>
            <div>
                <label for="contact-message">Message</label>
                <textarea id="contact-message" name="message"
                          rows="5" maxlength="5000" required></textarea>
            </div>
            <button type="submit">Send Message</button>
            <p id="contact-status" role="status" aria-live="polite"></p>
        </form>
    </div>
</section>
""")

    # -------------------------------------------------
    # FAQS
    # -------------------------------------------------

    if cleaned_faqs:
        html_parts.append('<section class="faq-section" id="faq">')
        html_parts.append('<div class="container">')
        html_parts.append("<h2>Frequently Asked Questions</h2>")

        for faq in cleaned_faqs:
            html_parts.append(
                f'<div class="faq-item">'
                f'<h3>{escape(faq["question"])}</h3>'
                f'<p>{escape(faq["answer"])}</p>'
                f'</div>'
            )

        html_parts.append("</div></section>")

    # -------------------------------------------------
    # CLOSE MAIN, THEN FOOTER
    # -------------------------------------------------

    html_parts.append("</main>")

    html_parts.append(f"""
<footer class="site-footer">
    <div class="container">
        <div class="footer-content">
            {escape(business_name)} — {escape(location)}
        </div>
    </div>
</footer>
""")

    # -------------------------------------------------
    # CONTACT FORM API INTEGRATION
    # -------------------------------------------------

    html_parts.append("""
<script>
(function () {
    const form = document.getElementById("contact-form");
    const status = document.getElementById("contact-status");

    if (!form || !status) return;

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const button = form.querySelector('button[type="submit"]');
        button.disabled = true;
        status.textContent = "Sending message...";

        // Expected preview URL: /local-page/<page_id>/preview
        const match = window.location.pathname.match(
            /\\/local-page\\/([a-fA-F0-9]+)\\/preview\\/?$/
        );

        if (!match) {
            status.textContent =
                "Page ID not found. Open this page using its Local Page Agent preview URL.";
            button.disabled = false;
            return;
        }

        const payload = {
            page_id: match[1],
            name: form.elements["name"].value.trim(),
            email: form.elements["email"].value.trim(),
            message: form.elements["message"].value.trim()
        };

        try {
            const response = await fetch("/local-page/contact", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            let result = {};
            try {
                result = await response.json();
            } catch (_) {
                result = {};
            }

            if (!response.ok) {
                const detail = result.detail;
                const message = Array.isArray(detail)
                    ? detail.map(item => item.msg || "Invalid input").join(", ")
                    : detail;

                throw new Error(message || "Unable to send your message.");
            }

            status.textContent = "Message sent successfully!";
            form.reset();
        } catch (error) {
            status.textContent =
                error.message || "Could not send message. Please try again.";
        } finally {
            button.disabled = false;
        }
    });
})();
</script>
""")

    html_parts.append("</body>")
    html_parts.append("</html>")

    return "\n".join(html_parts)
