import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
import time
import urllib.robotparser

visited = set()
results = []
titles = {}

bad_anchor_words = ["click here", "read more", "more", "link", "here"]

def classify_speed(ms):

    if ms < 100:
        return "Excellent"
    elif 100 <= ms <= 200:
        return "Good"
    elif 200 < ms <= 1000:
        return "Acceptable"
    else:
        return "Poor"


def crawler_score(status, speed_rating, robots_blocked):

    if robots_blocked:
        return "Blocked for Crawlers"

    if status != 200:
        return "Not Crawlable"

    if speed_rating in ["Excellent", "Good"]:
        return "Crawler Friendly"

    if speed_rating == "Acceptable":
        return "Needs Optimization"

    return "Poor for Crawling"


def check_robots(start_url):

    robots_url = urljoin(start_url, "/robots.txt")

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)

    try:
        rp.read()
    except:
        return None

    return rp


def check_page(url, domain, rp):

    try:

        start_time = time.time()

        r = requests.get(url, timeout=10)

        load_time = time.time() - start_time

        load_ms = int(load_time * 1000)

        speed_rating = classify_speed(load_ms)

        status = r.status_code

        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.title.string.strip() if soup.title else ""

        title_issue = ""
        if not title:
            title_issue = "Missing Title"

        if title in titles:
            title_issue = "Duplicate Title"
        else:
            titles[title] = url

        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_issue = ""
        if not meta_desc:
            meta_issue = "Missing Meta Description"

        canonical_tag = soup.find("link", rel="canonical")
        canonical = canonical_tag["href"] if canonical_tag else ""

        h1_tags = soup.find_all("h1")

        heading_issue = ""

        if len(h1_tags) == 0:
            heading_issue = "Missing H1"
        elif len(h1_tags) > 1:
            heading_issue = "Multiple H1"

        images = soup.find_all("img")
        missing_alt = 0

        for img in images:
            if not img.get("alt"):
                missing_alt += 1

        link_issue = ""
        accessibility_issue = ""

        internal_links = []

        for a in soup.find_all("a", href=True):

            text = a.get_text(strip=True).lower()

            if text in bad_anchor_words:
                link_issue = "Non descriptive link"

            if text == "":
                accessibility_issue = "Link missing accessible name"

            link = urljoin(url, a["href"])

            if urlparse(link).netloc == domain:
                internal_links.append(link)

        robots_blocked = ""

        if rp:
            if not rp.can_fetch("*", url):
                robots_blocked = "Yes"

        crawl_status = crawler_score(status, speed_rating, robots_blocked)

        results.append({

            "URL": url,
            "Status": status,
            "Load Time (ms)": load_ms,
            "Speed Rating": speed_rating,
            "Crawler Evaluation": crawl_status,
            "Title Issue": title_issue,
            "Meta Issue": meta_issue,
            "Canonical": canonical,
            "Heading Issue": heading_issue,
            "Images Missing ALT": missing_alt,
            "Link Issue": link_issue,
            "Accessibility Issue": accessibility_issue,
            "Blocked by Robots": robots_blocked
        })

        return internal_links

    except Exception as e:

        results.append({

            "URL": url,
            "Status": "Error",
            "Load Time (ms)": "",
            "Speed Rating": "",
            "Crawler Evaluation": "Error",
            "Title Issue": "",
            "Meta Issue": "",
            "Canonical": "",
            "Heading Issue": "",
            "Images Missing ALT": "",
            "Link Issue": "",
            "Accessibility Issue": str(e),
            "Blocked by Robots": ""
        })

        return []


def crawl(start_url, max_pages=100):

    domain = urlparse(start_url).netloc

    rp = check_robots(start_url)

    to_visit = [start_url]

    while to_visit and len(visited) < max_pages:

        url = to_visit.pop(0)

        if url in visited:
            continue

        print("Crawling:", url)

        visited.add(url)

        links = check_page(url, domain, rp)

        for link in links:
            if link not in visited:
                to_visit.append(link)

        time.sleep(1)

    df = pd.DataFrame(results)

    print("\nSEO Crawl Report\n")

    print(df)

    df.to_csv("seo_crawler_report.csv", index=False)

    print("\nReport saved as seo_crawler_report.csv")


crawl("https://goldenpestsolutions.com/")