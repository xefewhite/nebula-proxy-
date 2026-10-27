# Nebula Proxy

A blue-futuristic Flask starter website with server-side fetching for public HTML and plain-text URLs.

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Deploy with Docker

The Dockerfile uses Gunicorn. Add it to `requirements.txt` before building:

```text
gunicorn>=22,<24
```

Then:

```bash
docker build -t nebula-proxy .
docker run --rm -p 8080:8080 nebula-proxy
```

Open http://localhost:8080.

## Important limitations and security

- This is a starter implementation, not a production-grade anonymity service.
- It only returns HTML/plain text; scripts, images, forms, logins, streaming and many modern sites won't work.
- Private and non-public resolved IPs are rejected, and redirects are validated separately. DNS rebinding and other SSRF edge cases still require stronger network-level egress controls for public deployment.
- Do not expose this service publicly without authentication, rate limits, request logging/abuse controls, strict egress filtering, and security review. Public open proxies are frequently abused.
- The app intentionally strips forms and blocks active embedded content to reduce risk.
- Use only where you have permission and comply with the destination site's terms.

## Deploy online with Render

This project includes `render.yaml` for Render's free web-service plan.

1. Create a GitHub repository and upload the contents of this folder (the files should be at the repository root, not nested inside another folder).
2. Open https://render.com and sign in.
3. In Render, choose **New → Blueprint** and connect your GitHub repository.
4. Review the service named `nebula-proxy` and deploy it.
5. When the deployment finishes, open the `onrender.com` URL shown on the Render service page.

Free services can sleep after inactivity and may take a little time to wake up. Do not publish this as a public open proxy for unrestricted use; it needs stronger network-level protections, abuse prevention, and a security review before public use.
