import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = "439286e1d140746b7"
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
TO_ADDR = "tayalank.it20+jobautomation@gmail.com"

# Enhanced, diverse queries
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
        "num": 5,
        "sort": "date"
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        return resp.json().get("items", [])
    return []

def gemini_summarize(text, prompt):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": f"{prompt}\n\n{text}"}]}]
    }
    params = {"key": GEMINI_API_KEY}
    resp = requests.post(api_url, headers=headers, params=params, json=data)
    if resp.status_code == 200:
        try:
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            return ""
    else:
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
    """Try to get LinkedIn hiring manager profile or company careers email using Gemini (limited but best-effort)."""
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
    for query in SEARCH_QUERIES:
        results = search_google_jobs(query)
        for item in results:
            job_title = item.get("title", "No Title")
            link = item.get("link", "")
            if link in seen_links:
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
                "linkedin_url_or_email": linkedin_url_or_email
            })

    html = "<h2>Today's Fresh DevOps Job Openings</h2>"
    for i, job in enumerate(all_jobs, 1):
        html += f"<h3>{i}. {job['job_title']}</h3>"
        html += f"<p><b>Company:</b> {job['company']}<br>"
        html += f"<b>Description:</b> {job['desc']}<br>"
        html += f"<b>Apply:</b> <a href='{job['link']}'>Link</a></p>"
        html += f"<b>LinkedIn Outreach Message:</b><br><blockquote>{job['linkedin_msg']}</blockquote>"
        html += f"<b>LinkedIn/Email for Outreach:</b><br><blockquote>{job['linkedin_url_or_email']}</blockquote><hr>"

    send_email("Daily DevOps Job Digest", html, TO_ADDR)

if __name__ == "__main__":
    main()