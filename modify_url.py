import mitmproxy.http
import re


def load_domains(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return set(line.strip() for line in file.readlines())


DOMAINS_FILE = "./Client_Domains.txt"
ALLOWED_DOMAINS = load_domains(DOMAINS_FILE)


def response(flow: mitmproxy.http.HTTPFlow):
    url = flow.request.url
    parsed_url = re.search(r"https?://([^/]+)", url)

    if parsed_url:
        domain = parsed_url.group(1)

        
        if domain in ALLOWED_DOMAINS:
            if "text/html" in flow.response.headers.get("Content-Type", ""):
                if "tng_w=staging" not in url:
                    if "?" in url:
                        modified_url = url + "&tng_w=staging"
                    else:
                        modified_url = url + "?tng_w=staging"

                    
                    flow.response.headers["Refresh"] = f"0;url={modified_url}"
                    print(f"[REDIRECT] Перенаправление: {url} -> {modified_url}")
