import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def normalize_url(url):
    url = url.strip()
    if not url.startswith("http"):
        url = "http://" + url
    return url

def same_domain(base, target):
    return urlparse(base).netloc == urlparse(target).netloc

def crawl(base_url, max_pages=25):
    visited = set()
    queue = [base_url]

    data = {"urls": [], "forms": [], "scripts": []}

    while queue and len(visited) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            r = requests.get(url, timeout=8, allow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")
            data["urls"].append(url)

            for s in soup.find_all("script"):
                src = s.get("src")
                if src:
                    full = urljoin(url, src)
                    if full not in data["scripts"]:
                        data["scripts"].append(full)

            for f in soup.find_all("form"):
                action = f.get("action") or url
                method = (f.get("method") or "get").lower()
                action_url = urljoin(url, action)

                inputs = []
                for i in f.find_all(["input", "textarea", "select"]):
                    nm = i.get("name")
                    typ = i.get("type", "text")
                    if nm:
                        inputs.append({"name": nm, "type": typ})

                data["forms"].append({
                    "page": url,
                    "action": action_url,
                    "method": method,
                    "inputs": inputs
                })

            for a in soup.find_all("a", href=True):
                nxt = urljoin(url, a["href"]).split("#")[0]
                if nxt.startswith("http") and same_domain(base_url, nxt):
                    if nxt not in visited and nxt not in queue:
                        queue.append(nxt)
        except:
            continue

    return data
