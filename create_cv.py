import re
import os
from pathlib import Path
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# --- Configuration ---
HTML_FILE = "index.html"
TEMPLATE_FILE = "cv_template.html"
PDF_FILE = "./assets/Rohan_Posthumus_CV.pdf"


def get_inner_html(node):
    """
    Gets the inner HTML of a BeautifulSoup node as a clean string.
    """
    if not node:
        return ""
    # Get all child contents as a string
    text = "".join(str(c) for c in node.contents).strip()
    # Cleanup
    text = text.replace("<strong>", "<b>").replace("</strong>", "</b>")
    text = text.replace("<br>", "<br/>")
    # Clean up artifacts
    text = re.sub(r"</?span.*?>", "", text, flags=re.IGNORECASE)
    text = re.sub(r'style=".*?"', "", text, flags=re.IGNORECASE)
    return text


def scrape_data(soup):
    """Scrapes all data from the BeautifulSoup object and returns a dict."""
    data = {}

    try:
        # --- 1. Header & Contact ---
        # Note: Name is hardcoded as it's animated on the site
        data["name"] = "Rohan Posthumus"
        data["title"] = soup.find(id="cv-title").get_text(strip=True)

        data["contact"] = {
            "email": soup.find(id="cv-email")["href"].replace("mailto:", ""),
            "linkedin": soup.find(id="cv-linkedin")["href"],
            "github": soup.find(id="cv-github")["href"],
            "website": "https://rohanposthumus.github.io/rohanposthumus/",
        }

        # --- 2. Summary ---
        data["summary"] = soup.find(id="cv-summary").get_text(strip=True)

        # --- 3. Key Projects ---
        # This logic is already robust, as it's tied to the "projects" article id
        projects_article = soup.find("article", id="projects")
        data["projects"] = []
        for project in projects_article.find_all("h3"):
            data["projects"].append(
                {
                    "title": project.get_text(strip=True),
                    "details": get_inner_html(project.find_next_sibling("p")),
                }
            )

        # --- 4. Experience ---
        data["experience"] = []
        # Use the new stable ID
        exp_table = soup.find(id="cv-experience-table")
        for row in exp_table.find("tbody").find_all("tr"):
            cols = row.find_all("td")
            data["experience"].append(
                {
                    "title": cols[0].get_text(strip=True),
                    "employer": get_inner_html(cols[1]).replace("<br/>", ""),
                    "duration": get_inner_html(cols[2]).replace("<br/>", " • "),
                }
            )

        # --- 5. Education ---
        data["education"] = []
        # Use the new stable ID
        edu_table = soup.find(id="cv-education-table")
        for row in edu_table.find("tbody").find_all("tr"):
            cols = row.find_all("td")
            data["education"].append(
                {
                    "institution": cols[0].get_text(strip=True),
                    "qualification": cols[1].get_text(strip=True),
                    "year": cols[2].get_text(strip=True),
                }
            )

        # --- 6. Skills ---
        # Use the new stable ID
        skills_list = soup.find(id="cv-skills-list")
        data["skills"] = [li.get_text(strip=True) for li in skills_list.find_all("li")]

        # --- 7. Achievements ---
        # Use the new stable ID
        ach_list = soup.find(id="cv-achievements-list")
        data["achievements"] = [
            li.get_text(strip=True) for li in ach_list.find_all("li")
        ]

        return data

    except Exception as e:
        print(
            "Error: Could not parse HTML. Did the structure or IDs in 'index.html' change?"
        )
        print(f"Details: {e}")
        return None


def create_pdf():
    print(f"Reading '{HTML_FILE}'...")
    try:
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "lxml")
    except FileNotFoundError:
        print(f"Error: Could not find '{HTML_FILE}'.")
        return

    # --- 1. Scrape Data ---
    print("Scraping data from HTML...")
    data = scrape_data(soup)
    if not data:
        return

    # --- 2. Load Jinja Template ---
    print(f"Loading Jinja template from '{TEMPLATE_FILE}'...")
    try:
        env = Environment(loader=FileSystemLoader("."))  # Look in current folder
        template = env.get_template(TEMPLATE_FILE)
    except Exception as e:
        print(f"Error: Could not load template. {e}")
        return

    # --- 3. Render Template ---
    print("Injecting data into template...")
    html_output = template.render(data)

    # --- 4. Convert to PDF with WeasyPrint ---
    print(f"Generating '{PDF_FILE}'...")
    try:
        # WeasyPrint needs a 'base_url' to find relative paths
        # for CSS or images linked in your cv_template.html
        base_url = Path(TEMPLATE_FILE).resolve().parent.as_uri() + "/"

        HTML(string=html_output, base_url=base_url).write_pdf(PDF_FILE)

        print("Success! PDF created.")

    except Exception as e:
        print(f"An unexpected error occurred during PDF generation: {e}")


if __name__ == "__main__":
    create_pdf()
