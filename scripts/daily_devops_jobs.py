import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
import base64
from google import genai
import google.genai as genai


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = "439286e1d140746b7"
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
TO_ADDR = "tayalank.it20+jobautomation@gmail.com"

SEARCH_QUERIES = [
    'fresher DevOps jobs at startups',
    'fresher DevOps jobs at top startups',
    'fresher DevOps jobs at fast-growing startups',
    'junior DevOps engineer jobs at startups',
    'junior DevOps engineer jobs at top startups',
    'junior DevOps engineer jobs at fast-growing startups',
    'entry-level DevOps jobs at startups',
    'entry-level DevOps jobs at top startups',
    'entry-level DevOps jobs at fast-growing startups',
    'DevOps internship at startups',
    'DevOps internship at top startups',
    'DevOps internship at fast-growing startups',
    'graduate DevOps jobs at startups',
    'graduate DevOps jobs at top startups',
    'graduate DevOps jobs at fast-growing startups',
]

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

def gemini_summarize(text, prompt):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    try:
        response = model.generate_content(f"{prompt}\n\n{text}")
        return response.text if hasattr(response, 'text') else str(response)
    except Exception:
        return ""

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

def get_linkedin_and_email(job_title, company):
    prompt = f"Find either the LinkedIn profile URL of the hiring manager or recruiter, or the careers or HR email for a job titled '{job_title}' at '{company}' (if possible, else return 'Not found')."
    return gemini_summarize("", prompt)

def make_linkedin_message(job_title, company, link):
    prompt = (
        f"Write a personalized LinkedIn outreach message for a fresher/junior DevOps applicant. "
        f"Job Title: {job_title}\nCompany: {company}\nApplication Link: {link}. "
        "Make it polite, enthusiastic, and tailored for a first-time applicant."
    )
    return gemini_summarize("", prompt)

def main():
    all_jobs = []
    seen_links = set()
    now = datetime.now(timezone.utc)
    past_24h = now - timedelta(days=1)
    for query in SEARCH_QUERIES:
        results = search_google_jobs(query)
        for item in results:
            job_title = item.get("title", "No Title")
            link = item.get("link", "")
            if link in seen_links:
                continue
            job_date = parse_date_from_item(item)
            # Only include if published in last 24h or date unknown
            if job_date is not None and job_date < past_24h:
                continue
            seen_links.add(link)
            snippet = item.get("snippet", "")
            desc = gemini_summarize(snippet, "Summarize this job posting for a fresher DevOps applicant:")
            company = ""
            if "|" in job_title:
                parts = job_title.split("|")
                if len(parts) > 1:
                    company = parts[1].strip()
            linkedin_msg = make_linkedin_message(job_title, company, link)
            linkedin_url_or_email = get_linkedin_and_email(job_title, company)
            all_jobs.append({
                "job_title": job_title,
                "company": company,
                "link": link,
                "desc": desc,
                "linkedin_msg": linkedin_msg,
                "linkedin_url_or_email": linkedin_url_or_email,
                "job_date": job_date
            })

    html = "<h2>Today's Fresh DevOps Job Openings (Past 24H, or date unknown)</h2>"
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
        html += f"<b>Apply:</b> <a href='{job['link']}'>Link</a></p>"
        html += f"<b>LinkedIn Outreach Message:</b><br><blockquote>{job['linkedin_msg']}</blockquote>"
        html += f"<b>LinkedIn/Email for Outreach:</b><br><blockquote>{job['linkedin_url_or_email']}</blockquote><hr>"

    send_email("Daily DevOps Job Digest (Past 24H)", html, TO_ADDR)

if __name__ == "__main__":
    main()