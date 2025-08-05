import os
import shutil
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup


class WebsiteToFlask:
    def __init__(self, url, project_name="flask_project"):
        self.url = url
        self.project_name = project_name
        self.base_path = Path.cwd() / project_name
        self.templates_dir = self.base_path / "templates"
        self.static_dir = self.base_path / "static"

    def run(self):
        print("Downloading website...")
        site_folder = self.download_website()
        print("Organizing files...")
        self.organize_flask_project(site_folder)
        print("Creating Flask app...")
        self.create_basic_flask_app()
        print("Flask-ready project created at:", self.base_path)

    def download_website(self):
        output_folder = Path.cwd() / "downloaded_site"
        if output_folder.exists():
            shutil.rmtree(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        command = [
            "wget", "--mirror", "--convert-links", "--adjust-extension",
            "--page-requisites", "--no-parent", self.url, "-P", str(output_folder)
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Try to find main HTML folder
        domain = self.url.split("//")[-1].strip("/")
        downloaded_path = output_folder / domain

        if not downloaded_path.exists():
            html_files = list(output_folder.rglob("index.html"))
            if html_files:
                return html_files[0].parent
        return downloaded_path

    def organize_flask_project(self, site_folder):
        if self.base_path.exists():
            shutil.rmtree(self.base_path)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir.mkdir(parents=True, exist_ok=True)

        for file_path in site_folder.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(site_folder)
                ext = file_path.suffix.lower()

                if ext in [".html", ".htm"]:
                    dest = self.templates_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest)
                    self.update_html_references(dest)
                elif ext in [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".woff", ".woff2", ".ttf", ".eot"]:
                    dest = self.static_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest)

    def update_html_references(self, html_path):
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f, "html.parser")

        for tag in soup.find_all(["link", "script", "img"]):
            attr = "href" if tag.name == "link" else "src"
            if tag.has_attr(attr):
                url = tag[attr]
                if url.startswith("http") or url.startswith("{{"):
                    continue
                new_url = self.find_flask_url(url)
                if new_url:
                    tag[attr] = new_url

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

    def find_flask_url(self, url):
        ext = os.path.splitext(url)[-1].lower()
        if ext in [".css"]:
            return "{{ url_for('static', filename='" + url.lstrip("/").replace("\\", "/") + "') }}"
        elif ext in [".js"]:
            return "{{ url_for('static', filename='" + url.lstrip("/").replace("\\", "/") + "') }}"
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".svg"]:
            return "{{ url_for('static', filename='" + url.lstrip("/").replace("\\", "/") + "') }}"
        elif ext in [".woff", ".woff2", ".ttf", ".eot"]:
            return "{{ url_for('static', filename='" + url.lstrip("/").replace("\\", "/") + "') }}"
        return None

    def create_basic_flask_app(self):
        app_file = self.base_path / "app.py"
        requirements_file = self.base_path / "requirements.txt"
        template_files = list(self.templates_dir.rglob("*.html"))

        routes = ""
        for f in template_files:
            rel_path = f.relative_to(self.templates_dir)
            route_path = "/" if rel_path.name == "index.html" else f"/{rel_path.as_posix().replace('.html','')}"
            func_name = rel_path.stem.replace("-", "_").replace(".", "_")
            routes += f"""
@app.route('{route_path}')
def {func_name}():
    return render_template('{rel_path.as_posix()}')"""

        app_code = f"""from flask import Flask, render_template
app = Flask(__name__)

{routes}

if __name__ == '__main__':
    app.run(debug=True)
"""
        with open(app_file, "w") as f:
            f.write(app_code)

        with open(requirements_file, "w") as f:
            f.write("flask\nbs4\n")



if __name__ == "__main__":
    url = input("Enter website URL: ")
    name = input("Enter Flask project folder name: ") or "flask_project"
    WebsiteToFlask(url, name).run()

