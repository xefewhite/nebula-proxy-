from flask import Flask, request, Response, render_template_string
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import ipaddress
import socket

app = Flask(__name__)
TIMEOUT = 15
MAX_BYTES = 5 * 1024 * 1024
ALLOWED_SCHEMES = {"http", "https"}

PAGE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nebula Proxy</title>
<style>
:root{color-scheme:dark;--bg:#07111f;--panel:#0d1d32;--line:#1d3b5d;--blue:#48b9ff;--cyan:#70f2ff;--muted:#9bb3cc}
*{box-sizing:border-box}body{margin:0;min-height:100vh;font-family:Inter,ui-sans-serif,system-ui,Arial;background:radial-gradient(ellipse at 50% -15%,#123f70 0,transparent 48%),linear-gradient(160deg,#07111f,#030914 80%);color:#edf7ff}
main{max-width:980px;margin:auto;padding:48px 22px 36px}.top{display:flex;align-items:center;gap:12px;margin-bottom:54px}.logo{width:42px;height:42px;border:1px solid #3c9ddd;border-radius:14px;display:grid;place-items:center;background:linear-gradient(135deg,#173c68,#0b1b30);box-shadow:0 0 26px #168ee544;color:var(--cyan);font-size:22px}.brand{font-size:18px;font-weight:750;letter-spacing:.4px}.brand small{display:block;color:var(--muted);font-size:11px;font-weight:500;letter-spacing:2px;margin-top:3px}
.hero{text-align:center;margin-bottom:32px}.eyebrow{color:var(--cyan);font-size:12px;letter-spacing:3px;text-transform:uppercase}.hero h1{font-size:clamp(38px,7vw,68px);line-height:1.04;letter-spacing:-2.5px;margin:16px 0}.hero h1 span{background:linear-gradient(90deg,#fff,#63caff 55%,#a5f7ff);color:transparent;background-clip:text}.hero p{color:var(--muted);font-size:16px;line-height:1.7;max-width:600px;margin:0 auto}
.searchbox{padding:10px;display:flex;gap:10px;background:#0b1b2cdd;border:1px solid #275078;border-radius:19px;box-shadow:0 18px 60px #0005,0 0 35px #168ee51c;max-width:760px;margin:28px auto 16px}.searchbox input{flex:1;min-width:0;border:0;outline:0;background:transparent;color:white;padding:14px 12px;font-size:15px}.searchbox button{border:0;border-radius:12px;background:linear-gradient(135deg,#40aaff,#51e0ef);color:#061426;font-weight:800;padding:0 24px;cursor:pointer}.searchbox button:hover{filter:brightness(1.08)}.hint{text-align:center;color:#7895b3;font-size:12px}.error{max-width:760px;margin:18px auto;padding:14px 16px;border:1px solid #854a5a;background:#351b2a;border-radius:12px;color:#ffd7df}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:48px}.card{padding:20px;border:1px solid var(--line);border-radius:16px;background:linear-gradient(150deg,#10233a,#091727);min-height:136px}.icon{font-size:22px;color:var(--cyan)}.card h3{font-size:14px;margin:13px 0 7px}.card p{color:var(--muted);font-size:12px;line-height:1.6;margin:0}.notice{margin:32px auto 0;max-width:760px;border-top:1px solid #1a3048;padding-top:18px;color:#7993ae;font-size:12px;line-height:1.7;text-align:center}footer{text-align:center;color:#59748f;font-size:11px;margin-top:30px}
@media(max-width:650px){main{padding-top:26px}.top{margin-bottom:42px}.searchbox{flex-direction:column}.searchbox button{padding:15px}.cards{grid-template-columns:1fr}.hero h1{letter-spacing:-1.5px}}
</style>
</head>
<body><main>
<div class="top"><div class="logo">✦</div><div class="brand">NEBULA PROXY<small>PRIVATE WEB GATEWAY</small></div></div>
<section class="hero"><div class="eyebrow">✦ Explore beyond the ordinary</div><h1>Your web.<br><span>Your orbit.</span></h1><p>A sleek gateway for exploring the web. Enter a full website address to open it through your Nebula server.</p></section>
<form class="searchbox" method="get" action="/browse"><input name="url" type="text" placeholder="https://example.com" aria-label="Website URL" required><button type="submit">Launch ↗</button></form>
<div class="hint">Enter a complete URL, including https://</div>
<div class="cards"><article class="card"><div class="icon">◎</div><h3>Simple by design</h3><p>A clean, focused interface for entering a destination and getting started.</p></article><article class="card"><div class="icon">⌁</div><h3>Server-side fetching</h3><p>Requests are fetched by the server and returned to your browser.</p></article><article class="card"><div class="icon">◇</div><h3>Safer defaults</h3><p>Private network destinations and unsupported content types are blocked.</p></article></div>
<div class="notice">Use responsibly and only access sites you are authorized to use. This starter proxy is not an anonymity service, and destination sites may still identify requests. Many websites will not work because they use advanced JavaScript, logins, streaming, or strict security policies.</div><footer>NEBULA PROXY · BUILT FOR THE OPEN WEB</footer>
</main></body></html>
"""

def is_public_host(host):
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    if not infos:
        return False
    for info in infos:
        addr = ipaddress.ip_address(info[4][0].split("%")[0])
        if not addr.is_global:
            return False
    return True

def validate_url(raw):
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Enter a website address.")
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError("Only http:// and https:// addresses are supported.")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Please enter a valid public website address.")
    if parsed.port and not (1 <= parsed.port <= 65535):
        raise ValueError("Invalid port.")
    if not is_public_host(parsed.hostname):
        raise ValueError("That host is unavailable or points to a private network.")
    return raw

@app.get("/")
def home():
    return render_template_string(PAGE)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}, 200

@app.get("/browse")
def browse():
    target = ""
    upstream = None
    try:
        target = validate_url(request.args.get("url", ""))
        # Follow redirects manually so every destination is validated before connecting.
        for _ in range(6):
            upstream = requests.get(
                target,
                timeout=(5, TIMEOUT),
                allow_redirects=False,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; NebulaProxy/1.1)",
                    "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.1",
                },
                stream=True,
            )
            if upstream.is_redirect:
                location = upstream.headers.get("Location")
                upstream.close()
                upstream = None
                if not location:
                    raise ValueError("The destination returned a redirect without a destination URL.")
                target = validate_url(urljoin(target, location))
                continue
            break
        else:
            raise ValueError("The destination redirected too many times.")

        content_type = upstream.headers.get("Content-Type", "").lower()
        if not any(t in content_type for t in ("text/html", "text/plain", "application/xhtml+xml")):
            upstream.close()
            upstream = None
            return render_template_string(PAGE + '<div class="error">This starter proxy can only display HTML and plain text. The destination returned another content type.</div>'), 415

        chunks, total = [], 0
        for chunk in upstream.iter_content(65536):
            if not chunk:
                continue
            total += len(chunk)
            if total > MAX_BYTES:
                upstream.close()
                upstream = None
                return render_template_string(PAGE + '<div class="error">This page is larger than the 5 MB starter limit.</div>'), 413
            chunks.append(chunk)
        encoding = upstream.encoding or "utf-8"
        status_code = upstream.status_code
        upstream.close()
        upstream = None
        text_body = b"".join(chunks).decode(encoding, errors="replace")

        if "html" in content_type or "xhtml" in content_type:
            soup = BeautifulSoup(text_body, "html.parser")
            # Keep the page readable, but this starter cannot run destination JavaScript.
            for tag in soup.find_all(["script", "iframe", "object", "embed", "form"]):
                tag.decompose()
            for tag in soup.find_all(["a"]):
                href = tag.get("href")
                if href:
                    absolute = urljoin(target, href)
                    if urlparse(absolute).scheme in ALLOWED_SCHEMES:
                        tag["href"] = "/browse?" + urlencode({"url": absolute})
            for tag in soup.find_all(["img", "link", "source", "video", "audio"]):
                attr = "src" if tag.name != "link" else "href"
                val = tag.get(attr)
                if val and val.startswith(("http://", "https://", "//")):
                    tag[attr] = "#"
            return Response(
                str(soup), status=status_code,
                content_type="text/html; charset=utf-8",
                headers={
                    "X-Content-Type-Options": "nosniff",
                    "Content-Security-Policy": "default-src 'none'; img-src 'none'; style-src 'unsafe-inline'; form-action 'none'; base-uri 'none'",
                },
            )
        return Response(text_body, status=status_code, content_type="text/plain; charset=utf-8", headers={"X-Content-Type-Options": "nosniff"})

    except (ValueError, requests.RequestException) as exc:
        message = str(exc)[:240] or "The destination could not be loaded."
        safe_message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return render_template_string(PAGE + '<div class="error"><strong>Could not load that page.</strong><br>' + safe_message + '</div>'), 400
    finally:
        if upstream is not None:
            upstream.close()

if __name__ == "__main__":
    # Local development only. Put behind a production WSGI server for deployment.
    app.run(host="127.0.0.1", port=5000, debug=False)
