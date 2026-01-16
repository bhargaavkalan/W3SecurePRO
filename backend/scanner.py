import requests
from urllib.parse import urljoin

SEC_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "Permissions-Policy"
]

SENSITIVE_PATHS = [
    "/.env",
    "/robots.txt",
    "/admin",
    "/backup.zip",
    "/phpinfo.php",
    "/.git/config"
]

def scan_headers(url):
    r = requests.get(url, timeout=8, allow_redirects=True)
    h = dict(r.headers)
    missing = [x for x in SEC_HEADERS if x not in h]
    return {
        "status_code": r.status_code,
        "server": h.get("Server", "Not Disclosed"),
        "missing": missing
    }

def scan_cors(url):
    r = requests.get(url, timeout=8, allow_redirects=True)
    acao = r.headers.get("Access-Control-Allow-Origin", "")
    return {
        "acao": acao if acao else "Not present",
        "bad": (acao == "*")
    }

def scan_sensitive(base):
    found = []
    for p in SENSITIVE_PATHS:
        try:
            u = urljoin(base, p)
            r = requests.get(u, timeout=5, allow_redirects=True)
            if r.status_code in [200, 206]:
                found.append(u)
        except:
            pass
    return found

def client_report(headers, cors, sensitive):
    report = []
    if headers["missing"]:
        report.append({
            "title": "Missing Security Headers",
            "severity": "Medium",
            "explain": "Your website is missing browser level security protection. This increases attack risk.",
            "fix": "Add recommended security headers in server configuration."
        })
    if cors["bad"]:
        report.append({
            "title": "CORS Misconfiguration",
            "severity": "High",
            "explain": "Your website allows any external website to request data. This may expose user data.",
            "fix": "Restrict CORS to only trusted domains."
        })
    if sensitive:
        report.append({
            "title": "Sensitive Files Exposed",
            "severity": "High",
            "explain": "Internal or configuration files are accessible from the internet. This can leak secrets.",
            "fix": "Block access to these files and remove backups."
        })
    if not report:
        report.append({
            "title": "No Major Issues Found",
            "severity": "Low",
            "explain": "No critical issues were detected in passive security checks.",
            "fix": "Continue monitoring and regular updates."
        })
    return report
