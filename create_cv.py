import re
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
import pdfkit

# --- Configuration ---
HTML_FILE = "index.html"
TEMPLATE_FILE = "cv_template.html"
PDF_FILE = "./assets/Rohan_Posthumus_CV.pdf"

path_to_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)


def get_inner_html(node):
    """
    Gets the inner HTML of a BeautifulSoup node as a clean string.
    This is more robust than regex on the outer tag.
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
        header_container = soup.find("div", class_="container")
        data["name"] = "Rohan Posthumus"  # Animated, so hardcode
        data["title"] = (
            header_container.find("h1").find_next_sibling("span").get_text(strip=True)
        )

        contact_icons = soup.find("article", id="contact").find("ul", class_="icons")
        data["contact"] = {
            "email": contact_icons.find("a", class_="fa-envelope")["href"].replace(
                "mailto:", ""
            ),
            "linkedin": contact_icons.find("a", class_="fa-linkedin")["href"],
            "github": contact_icons.find("a", class_="fa-github")["href"],
        }

        # --- 2. Summary ---
        about_article = soup.find("article", id="about")
        data["summary"] = about_article.find("blockquote").get_text(strip=True)

        # --- 3. Key Projects ---
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
        exp_table = about_article.find("h3", string="Experience").find_next("table")
        for row in exp_table.find("tbody").find_all("tr"):
            cols = row.find_all("td")
            data["experience"].append(
                {
                    "title": cols[0].get_text(strip=True),
                    "employer": get_inner_html(cols[1]).replace("<br/>", ", "),
                    "duration": get_inner_html(cols[2]).replace("<br/>", " - "),
                }
            )

        # --- 5. Education ---
        data["education"] = []
        edu_table = about_article.find("h3", string="Formal education").find_next(
            "table"
        )
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
        skills_list = about_article.find("h3", string="Top 10 skills").find_next("ul")
        data["skills"] = [li.get_text(strip=True) for li in skills_list.find_all("li")]

        # --- 7. Achievements ---
        ach_list = about_article.find("h3", string="Recent achievements").find_next(
            "ul"
        )
        data["achievements"] = [
            li.get_text(strip=True) for li in ach_list.find_all("li")
        ]

        return data

    except Exception as e:
        print("Error: Could not parse HTML. Did the structure of 'index.html' change?")
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

    # --- 4. Convert to PDF ---
    print(f"Generating '{PDF_FILE}'...")
    try:
        options = {
            "page-size": "A4",
            "margin-top": "2cm",
            "margin-right": "1.5cm",
            "margin-bottom": "2cm",
            "margin-left": "1.5cm",
            "encoding": "UTF-8",
            "quiet": "",  # Suppresses console output
            "footer-right": "Page [page] of [topage]",
            "footer-line": True,
            "footer-font-size": "8",
        }

        pdfkit.from_string(
            html_output, PDF_FILE, configuration=PDFKIT_CONFIG, options=options
        )
        print("Success! PDF created.")

    except IOError as e:
        if "No wkhtmltopdf executable found" in str(e):
            print("--- PDFkit Error ---")
            print(f"Could not find 'wkhtmltopdf.exe' in '{path_to_wkhtmltopdf}'")
            print(
                "Please make sure you have installed it and the path at the top of the script is correct."
            )
        else:
            print(f"Error: Could not build PDF. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    create_pdf()
