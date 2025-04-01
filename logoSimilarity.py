
import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import imagehash
import networkx as nx

# Converting domains into valid URLs #
def make_domain_to_url(domain):
    return f"https://{domain.strip()}/"

# Reading domains from input files ===
def get_url_sites(file):
    input = pd.read_parquet(file, engine='pyarrow')
    return sorted(set(input["domain"].apply(make_domain_to_url)))

#  Extracting the logo URL ===
def extract_logo_url_selenium(website_url):
    driver = None
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36")
    service = Service(r"C:\\Users\\Geani\\chromedriver-win64\\chromedriver.exe")

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(15)
        driver.get(website_url)

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "img")))
        except:
            print(f" {website_url} we don't have <img> in DOM. We continue the process.")

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        base_url = driver.current_url + "/"

        for img in soup.find_all("img"):
            alt = img.get("alt", "").lower()
            cls = " ".join(img.get("class", [])).lower()
            src = img.get("src", "").lower()
            if "logo" in alt or "logo" in cls or "logo" in src:
                return urljoin(base_url, src)

        for svg in soup.find_all("svg"):
            svg_class = " ".join(svg.get("class", [])).lower()
            svg_id = svg.get("id", "").lower()
            if "logo" in svg_class or "logo" in svg_id:
               # print("[✓] Găsit <svg> cu clasă 'logo' – inline SVG")
                return f"[inline SVG logo] – {website_url}"

        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return urljoin(base_url, og_image["content"])

        icon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
        if icon and icon.get("href"):
            return urljoin(base_url, icon.get("href"))

    except Exception as e:
        print(f"Error when accesing {website_url}: {e}")
    finally:
        if driver:
            driver.quit()

    return None

#  Downloading and saving the logo image ===
def save_logo_image(logo_url, domain):
    try:
        if logo_url.startswith("data:image"):
          #  print(f"[⏭️] Imagine inline base64, sar peste {domain}")
            return None

        if not os.path.exists("logos"):
            os.makedirs("logos")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://www.google.com/"
        }
        response = requests.get(logo_url, headers=headers, timeout=7)
        if response.status_code == 200:
            image_path = os.path.join("logos", f"{domain}.png")
            with open(image_path, "wb") as f:
                f.write(response.content)
           # print(f" Image save: {image_path}")
            return image_path
        else:
           # print(f"[!] Error HTTP: {response.status_code} for {logo_url}")
            return None
    except Exception as e:
       # print(f"Error when trying to download the logo {logo_url}: {e}")
        return None

# Generating visual hashes for logos ===
def generate_hashes_from_folder(folder="logos"):
    hashes = {}
    for filename in os.listdir(folder):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            domain = filename.rsplit(".", 1)[0]
            image_path = os.path.join(folder, filename)
            try:
                img = Image.open(image_path).convert("RGB")
                hash_val = imagehash.phash(img)
                hashes[domain] = hash_val
            except Exception as e:
                print(f"Error at {filename}: {e}")
    return hashes

# Building the similarity graph and grouping websites ===
def build_similarity_graph(hashes, threshold=5):
    G = nx.Graph()
    domains = list(hashes.keys())
    G.add_nodes_from(domains)
    for i in range(len(domains)):
        for j in range(i + 1, len(domains)):
            h1, h2 = hashes[domains[i]], hashes[domains[j]]
            if abs(h1 - h2) <= threshold:
                G.add_edge(domains[i], domains[j])
              #  print(f"[=] {domains[i]} ↔ {domains[j]} (diff: {abs(h1 - h2)})")
    return G


def extract_logo_groups(graph):
    groups = list(nx.connected_components(graph))
    for idx, group in enumerate(groups):
        print(f"Group {idx + 1}: {group}")
    return groups


# def log_error(domain, message):
#     with open("erori.log", "a", encoding="utf-8") as log_file:
#         log_file.write(f"{domain} - {message}\n")


if __name__ == "__main__":
    url_sites = get_url_sites("logos.snappy.parquet")  # TOATE domeniile
    total = len(url_sites)

    # for idx, site_url in enumerate(url_sites, 1):
    #     domain = site_url.split("//")[-1].strip("/")
    #     image_path = os.path.join("logos", f"{domain}.png")

    #    # print(f"\n[→] Procesăm {idx}/{total}: {domain}")

    #     if os.path.exists(image_path):
    #       #  print(f" Logo deja salvat pentru {domain}, sar peste.")
    #         continue


    print("\n Generate saved hash codes")
    hashes = generate_hashes_from_folder("logos")
    print(f"[i] Generate {len(hashes)} hash codes.")

    # print("\n Construim graful de similaritate între logo-uri...")
    graph = build_similarity_graph(hashes, threshold=5)
    print(f"[i] Number of nodes in graph : {len(graph.nodes)}")
    print(f"[i] Number of connections (similarities): {len(graph.edges)}")

    print("\n Groups of logo similarities:")
    groups = extract_logo_groups(graph)
    print(f"Total Groups: {len(groups)}")
