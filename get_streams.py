import re, json, base64, requests, random, sys
from urllib.parse import quote

BASE = "https://gemma416okl.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

PROXIES = [
    ("31.59.20.176",    6754),
    ("31.56.127.193",   7684),
    ("45.38.107.97",    6014),
    ("38.154.203.95",   5863),
    ("198.105.121.200", 6462),
    ("64.137.96.74",    6641),
    ("198.23.243.226",  6361),
    ("38.154.185.97",   6370),
    ("142.111.67.146",  5611),
    ("191.96.254.138",  6185),
]
PROXY_USER = "ygxmhkcc"
PROXY_PASS = "n3batopqanpg"

def make_session(host, port):
    proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{host}:{port}"
    s = requests.Session()
    s.proxies = {"http": proxy_url, "https": proxy_url}
    s.headers["User-Agent"] = UA
    return s

def get_streams(imdb_id="tt0800369"):
    referer = f"{BASE}/play/{imdb_id}"

    proxy_list = PROXIES.copy()
    random.shuffle(proxy_list)
    s, html = None, None
    for host, port in proxy_list:
        try:
            print(f"[*] Trying {host}:{port} ...", flush=True)
            s = make_session(host, port)
            r = s.get(referer, timeout=15)
            if r.status_code == 200:
                html = r.text
                print(f"[+] Connected via {host}:{port}")
                break
        except Exception as e:
            print(f"    failed: {e}")

    if not html:
        print("[-] All proxies failed.")
        sys.exit(1)

    m = re.search(r'let\s+p3\s*=\s*(\{.+?\});', html, re.DOTALL)
    if not m:
        print("[-] Config block not found in page.")
        sys.exit(1)

    cfg = json.loads(m.group(1))
    token, file_path = cfg["key"], cfg["file"]
    print(f"[+] Token: {token[:30]}...")
    print(f"[+] File:  {file_path[:60]}...")

    def post(url):
        r = s.post(url, data="", headers={
            "X-CSRF-Token": token,
            "Referer": referer,
            "Origin": BASE,
            "Content-Type": "application/x-www-form-urlencoded",
        }, timeout=15)
        raw = r.content
        try:
            d = base64.b64decode(raw).decode()
            if d[0] in "[{#h":
                return d
        except:
            pass
        return raw.decode()

    try:
        raw_tracks = json.loads(post(file_path))
    except Exception as e:
        print(f"[-] Failed to fetch/parse tracks: {e}")
        sys.exit(1)

    def flatten(obj):
        if isinstance(obj, dict):
            return [obj]
        if isinstance(obj, list):
            result = []
            for item in obj:
                result.extend(flatten(item))
            return result
        return []

    tracks = [t for t in flatten(raw_tracks) if t.get("file")]
    print(f"[+] {len(tracks)} track(s) found\n")

    for t in tracks:
        fp   = t.get("file", "")
        lang = t.get("title", "?")
        pl   = (fp[1:] + ".txt") if fp.startswith("~") else fp
        pl_url = f"{BASE}/playlist/{quote(pl, safe='')}"
        try:
            raw = post(pl_url).strip()
            print(f"[{lang}]")
            print(raw[:500])
            print()
        except Exception as e:
            print(f"[{lang}] ERROR: {e}\n")

if __name__ == "__main__":
    imdb_id = sys.argv[1] if len(sys.argv) > 1 else "tt0800369"
    get_streams(imdb_id)