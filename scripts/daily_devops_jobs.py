import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
import base64
import os
from google import genai
from google.genai import types
import google.genai as genai


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = "439286e1d140746b7"
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
TO_ADDR = "tayalank.it20+jobautomation@gmail.com"

# --- PERSONAL CONTEXT ---
PERSONAL_CONTEXT = """
Name: Ankit Tayal
Role Seeking: DevOps Engineer / Backend Developer (Java + Spring Boot)
Current Role: Agentic AI Engineer @ Prodigal AI
Location: Delhi NCR, India
Education: B.Tech in Industrial Internet of Things - GGSIPU
Certifications: AWS Certified Cloud Practitioner (CLF-C02), GitHub Foundations, Oracle Cloud Infrastructure 2025 Foundations Associate
Skills & Tools: Java, Python, JavaScript; AWS, GCP, Azure; Docker, Kubernetes, Terraform, Jenkins, GitHub Actions, Ansible, Prometheus, Grafana, Bash, Linux; Spring Boot, MongoDB, PostgreSQL, OAuth2, Kafka, REST APIs
Notable Projects: Journal App (Spring Boot, JWT/OAuth2, MongoDB, Kafka), CI/CD Full Stack Deployment (Docker, Travis CI, AWS EB, GCP GKE), Unified Academic Services Platform (Python, Django, AWS, PostgreSQL)
Experience Highlights: Designed LLM inference pipelines (Prodigal AI), Built real-time stock data visualizations & analytics pipelines (StockGro)
Leadership: Co-Lead, Cloud Computing @ Google Developer Student Club USAR
"""

SEARCH_QUERIES = [
    'fresher "DevOps" jobs at top startups in ("Delhi NCR" OR "Gurugram" OR "Noida")',
    'junior "DevOps" engineer jobs at top startups in ("Delhi NCR" OR "Gurugram" OR "Noida")',
    'entry-level "DevOps" jobs at startups in ("Delhi NCR" OR "Gurugram" OR "Noida")'
]

"""
    'junior DevOps engineer jobs at startups',
    'junior DevOps engineer jobs at fast-growing startups',
    'fresher DevOps jobs at fast-growing startups',
    'fresher DevOps jobs at startups',
    'entry-level DevOps jobs at startups',
    'entry-level DevOps jobs at fast-growing startups',
    'DevOps internship at startups',
    'DevOps internship at top startups',
    'DevOps internship at fast-growing startups',
    'graduate DevOps jobs at startups',
    'graduate DevOps jobs at top startups',
    'graduate DevOps jobs at fast-growing startups',
"""
# Gemini 2.5 Pro client setup
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)

def gemini_25pro(prompt):
    client = get_gemini_client()
    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        response_mime_type="text/plain",
    )
    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if hasattr(chunk, "text") and chunk.text is not None:
            response_text += chunk.text
    return response_text.strip()

def search_google_jobs(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_CSE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": 10,
        "sort": "date"
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        return resp.json().get("items", [])
    return []

def parse_date_from_item(item):
    pagemap = item.get("pagemap", {})
    # Try metatags
    if "metatags" in pagemap:
        for meta in pagemap.get("metatags", []):
            for k in meta:
                if k.lower() in ["article:published_time", "datepublished", "pubdate", "date"]:
                    try:
                        return datetime.fromisoformat(meta[k].replace("Z", "+00:00"))
                    except Exception:
                        continue
    # Try newsarticle objects
    if "newsarticle" in pagemap:
        for news in pagemap.get("newsarticle", []):
            for k in news:
                if k.lower() in ["datepublished", "datemodified"]:
                    try:
                        return datetime.fromisoformat(news[k].replace("Z", "+00:00"))
                    except Exception:
                        continue
    # Fallback: not found
    return None

def send_email(subject, html_body, to_addr):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    server.sendmail(GMAIL_ADDRESS, to_addr, msg.as_string())
    server.quit()

def summarize_job(snippet):
    prompt = f"max 150 words, Summarize this job posting for a fresher DevOps applicant:\n\n{snippet}"
    return gemini_25pro(prompt)


# def extract_job_posting_url(item):
#     pagemap = item.get("pagemap", {})
#     # Prefer job posting URLs from pagemap if available
#     if "metatags" in pagemap:
#         for meta in pagemap["metatags"]:
#             for key, value in meta.items():
#                 if "joburl" in key.lower() or "apply" in key.lower():
#                     return value
#     # Check for og:url or canonical
#     if "metatags" in pagemap:
#         for meta in pagemap["metatags"]:
#             for key, value in meta.items():
#                 if key.lower() in ["og:url", "twitter:url", "canonical"]:
#                     return value
#     if "jobposting" in pagemap:
#         for job in pagemap["jobposting"]:
#             for key, value in job.items():
#                 if "url" in key.lower():
#                     return value
#     return item.get("link", "")

# def get_linkedin_and_email(job_title, company):
#     prompt = (
#         f"Find either the LinkedIn profile URL of the hiring manager or recruiter, "
#         f"or the careers or HR email for a job titled '{job_title}' at '{company}' (if possible, else return 'Not found')."
#     )
#     return gemini_25pro(prompt)

# def make_linkedin_message(job_title, company, link):
#     prompt = (
#         f"max 150 words, Write a personalized LinkedIn outreach message for a fresher/junior DevOps applicant. "
#         f"Job Title: {job_title}\nCompany: {company}\nApplication Link: {link}. "
#         "Make it polite, enthusiastic, and tailored for a first-time applicant."
#     )
#     return gemini_25pro(prompt)

# --- FIND RECRUITER CONTACT USING GOOGLE SEARCH ---
def find_recruiter_contact(company):
    contact_queries = [
        f"{company} recruiter LinkedIn",
        f"{company} HR LinkedIn",
        f"{company} careers email",
        f"{company} hiring manager LinkedIn",
    ]
    for q in contact_queries:
        results = search_google_jobs(q)
        if results:
            res = results[0]
            return f"<a href='{res.get('link')}'>{res.get('title')}</a>"
    return "Not found."

# --- MAKE LINKEDIN MESSAGE (≤150 words, PERSONALIZED) ---
def make_linkedin_message(job_title, company, link, job_desc):
    prompt = (
        f"Write a highly personalized LinkedIn message (max 150 words) for a DevOps Engineer or Backend Developer opportunity, "
        f"using this context:\n{PERSONAL_CONTEXT}\n\n"
        f"Target job: {job_title} at {company}\nJob description: {job_desc}\n"
        f"Application link: {link}\n"
        "The message should be concise, polite, enthusiastic, fresher-friendly, and highlight how my background fits the role."
    )
    return gemini_25pro(prompt)

# --- MAIN LOGIC ---
def main():
    all_jobs = []
    seen_links = set()
    now = datetime.now(timezone.utc)
    past_24h = now - timedelta(days=1)
    for query in SEARCH_QUERIES:
        results = search_google_jobs(query)
        print(f"Found {len(results)} results for query: {query}")
        for item in results:
            job_title = item.get("title", "No Title")
            link = item.get("link", "")
            # link = extract_job_posting_url(item)
            if link in seen_links:
                continue
            job_date = parse_date_from_item(item)
            # Only include if published in last 24h or date unknown
            if job_date is not None and job_date < past_24h:
                continue
            seen_links.add(link)
            snippet = item.get("snippet", "")
            desc = summarize_job(snippet)
            company = ""
            if "|" in job_title:
                parts = job_title.split("|")
                if len(parts) > 1:
                    company = parts[1].strip()
            # linkedin_msg = make_linkedin_message(job_title, company, link)
            # linkedin_url_or_email = get_linkedin_and_email(job_title, company)
            linkedin_msg = make_linkedin_message(job_title, company, link, desc)
            recruiter_contact = find_recruiter_contact(company)
            all_jobs.append({
                "job_title": job_title,
                "company": company,
                "link": link,
                "desc": desc,
                "linkedin_msg": linkedin_msg,
                # "linkedin_url_or_email": linkedin_url_or_email,
                "recruiter_contact": recruiter_contact,
                "job_date": job_date
            })
            print(f"Added job: {job_title} at {company} - Date: {job_date} Link: {link}")

    # --- SUMMARY TABLE ---
    summary_html = """
    <h2>Job Summary Table</h2>
    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>Job Title</th>
            <th>Company</th>
            <th>Apply Link (Visible)</th>
        </tr>
    """
    for job in all_jobs:
        summary_html += f"""
        <tr>
            <td>{job['job_title']}</td>
            <td>{job['company']}</td>
            <td>
                <a href="{job['link']}" target="_blank">{job['link']}</a><br>
            </td>
        </tr>
        """
    summary_html += "</table><br>"

    # --- FULL EMAIL BODY ---
    html = summary_html
    html += "<h2>Today's Fresh DevOps Job Openings (Past 24H, or date unknown)</h2>"
    if not all_jobs:
        html += "<p>No new jobs found in the last 24 hours (or with a known date).</p>"
    for i, job in enumerate(all_jobs, 1):
        if job["job_date"]:
            date_str = job["job_date"].strftime("%Y-%m-%d %H:%M")
        else:
            date_str = "<i>Date unknown - may be recent</i>"
        html += f"<h3>{i}. {job['job_title']}</h3>"
        html += f"<p><b>Company:</b> {job['company']}<br>"
        html += f"<b>Description:</b> {job['desc']}<br>"
        html += f"<b>Posted:</b> {date_str}<br>"
        html += f"<b>Apply:</b> <a href='{job['link']}'>{job['link']}</a></p>"
        html += f"<b>LinkedIn Outreach Message:</b><br><blockquote>{job['linkedin_msg']}</blockquote>"
        html += f"<b>Recruiter/HR Contact:</b><br><blockquote>{job['recruiter_contact']}</blockquote><hr>"

    send_email("Daily DevOps Job Digest (Past 24H)", html, TO_ADDR)

    # html = "<h2>Today's Fresh DevOps Job Openings (Past 24H, or date unknown)</h2>"
    # if not all_jobs:
    #     html += "<p>No new jobs found in the last 24 hours (or with a known date).</p>"
    # for i, job in enumerate(all_jobs, 1):
    #     if job["job_date"]:
    #         date_str = job["job_date"].strftime("%Y-%m-%d %H:%M")
    #     else:
    #         date_str = "<i>Date unknown - may be recent</i>"
    #     html += f"<h3>{i}. {job['job_title']}</h3>"
    #     html += f"<p><b>Company:</b> {job['company']}<br>"
    #     html += f"<b>Description:</b> {job['desc']}<br>"
    #     html += f"<b>Posted:</b> {date_str}<br>"
    #     html += f"<b>Apply:</b> <a href='{job['link']}'>Link</a></p>"
    #     html += f"<b>LinkedIn Outreach Message:</b><br><blockquote>{job['linkedin_msg']}</blockquote>"
    #     # html += f"<b>LinkedIn/Email for Outreach:</b><br><blockquote>{job['linkedin_url_or_email']}</blockquote><hr>"
    #     html += f"<b>Recruiter/HR Contact:</b><br><blockquote>{job['recruiter_contact']}</blockquote><hr>"

    # send_email("Daily DevOps Job Digest (Past 24H)", html, TO_ADDR)

if __name__ == "__main__":
    main()