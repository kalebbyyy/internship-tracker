import os
import re
import json
from datetime import datetime
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing or empty.")

client = genai.Client(api_key=API_KEY)

COMPANIES = [
    "Mott Macdonald", "Metis", "Atkins", "AKT II", "Arup", "Arcadis",
    "Buro Happold", "Balfour Beatty", "WSP", "Laing O'Rourke", "Aecom",
    "COWI", "Mace", "TFL", "Skanska", "Robert Bird Group", "Network Rail",
    "Ferrovial", "Costain Group", "Burns and McDonnell", "Ramboll",
    "Stantec", "Waterman Group", "Kier Group", "Morgan Sindall",
    "Jacobs", "VolkerFitzpatrick"
]

prompt = f"""
Search official UK early careers portals (Bright Network, Gradcracker, company career sites) to determine whether undergraduate Summer 2027 internships or summer placements are currently OPEN or CLOSED in London for each of these companies:
{', '.join(COMPANIES)}

Important details to keep in mind:
- Arcadis has live London Summer 2027 listings (e.g. Transport Planner, Quantity Surveyor) open on Bright Network and Arcadis Early Careers.
- AECOM has dual-track student placement streams open in London that accept summer interns.

Return ONLY a valid JSON array of objects with the exact schema:
[
  {{
    "company": "Company Name",
    "status": "OPEN" | "CLOSED",
    "notes": "Specific open role title(s) if open, or expected release window if closed",
    "link": "Direct link or aggregator portal URL"
  }}
]
"""

Rules:
1. ONLY filter for Summer Internships located in London (UK). Do not count 12-month industrial placements or non-London roles.
2. Return ONLY a valid JSON array of objects with the exact schema:
[
  {{
    "company": "Company Name",
    "status": "OPEN" | "CLOSED",
    "notes": "Short description of role or expected opening window",
    "link": "Direct careers link or portal URL"
  }}
]
"""

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            response_mime_type="application/json"
        )
    )
    raw_text = response.text.strip()
    # Strip markdown if returned
    raw_text = re.sub(r"^```(?:json)?", "", raw_text, flags=re.MULTILINE)
    raw_text = re.sub(r"```$", "", raw_text, flags=re.MULTILINE).strip()
    data = json.loads(raw_text)
except Exception as e:
    print(f"Error querying Gemini or parsing JSON: {e}")
    data = [{"company": c, "status": "CLOSED", "notes": "Status check pending next cycle", "link": ""} for c in COMPANIES]

rows = ""
for item in data:
    status = str(item.get("status", "CLOSED")).upper()
    badge_class = "badge-open" if status == "OPEN" else "badge-closed"
    link = item.get("link", "")
    link_html = f'<a href="{link}" target="_blank">View Portal &rarr;</a>' if link and link.startswith("http") else "-"
    
    rows += f"""
    <tr>
      <td><strong>{item.get('company', '')}</strong></td>
      <td><span class="badge {badge_class}">{status}</span></td>
      <td>{item.get('notes', '')}</td>
      <td>{link_html}</td>
    </tr>
    """

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>London Summer 2027 Internships</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f172a;
      color: #f8fafc;
      padding: 24px;
      margin: 0;
    }}
    .container {{
      max-width: 1000px;
      margin: 0 auto;
    }}
    header {{
      margin-bottom: 24px;
    }}
    h1 {{
      font-size: 1.8rem;
      margin-bottom: 6px;
    }}
    p.sub {{
      color: #94a3b8;
      font-size: 0.9rem;
      margin-top: 0;
    }}
    .table-card {{
      background: #1e293b;
      border-radius: 12px;
      overflow-x: auto;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }}
    th, td {{
      padding: 14px 18px;
      border-bottom: 1px solid #334155;
      font-size: 0.92rem;
    }}
    th {{
      background: #172033;
      color: #94a3b8;
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 0.05em;
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
    tr:hover {{
      background: #243248;
    }}
    .badge {{
      padding: 4px 10px;
      border-radius: 9999px;
      font-weight: 700;
      font-size: 0.75rem;
      display: inline-block;
    }}
    .badge-open {{
      background: #10b981;
      color: #ffffff;
    }}
    .badge-closed {{
      background: #475569;
      color: #cbd5e1;
    }}
    a {{
      color: #38bdf8;
      text-decoration: none;
      font-weight: 500;
    }}
    a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>London Summer 2027 Internships</h1>
      <p class="sub">Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} (Auto-checked via Gemini)</p>
    </header>
    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>Company</th>
            <th>Status</th>
            <th>Notes</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""

os.makedirs("public", exist_ok=True)
with open("public/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Dashboard built successfully in public/index.html")
