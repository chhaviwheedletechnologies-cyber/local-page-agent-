
import json
import webbrowser
from pathlib import Path

from services.html_generator import generate_html

json_path = Path("generated_page.json")
html_path = Path("noida.html")

if not json_path.exists():
    print("generated_page.json nahi mili.")
    print("Pehle API response se page_content aur schema_markup save karna hoga.")
    raise SystemExit(1)

data = json.loads(
    json_path.read_text(encoding="utf-8")
)

html_content = generate_html(
    business_name=data["business_name"],
    location=data["location"],
    page_content=data["page_content"],
    schema_markup=data["schema_markup"],
)

html_path.write_text(
    html_content,
    encoding="utf-8"
)

print(f"HTML page saved: {html_path.resolve()}")

webbrowser.open(
    html_path.resolve().as_uri()
)