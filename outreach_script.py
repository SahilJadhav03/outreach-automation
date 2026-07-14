#!/usr/bin/env python3
"""
Automated Cold Email Outreach System
Runs daily via GitHub Actions to send personalized cold emails using Google Sheets,
BeautifulSoup scraping, Google Gemini AI, and Gmail SMTP.
"""

import os
import time
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from bs4 import BeautifulSoup
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SHEET_COLUMNS = [
    "First Name", "Last Name", "Email", "Company", "Website", "Date Sent"
]

SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

GEMINI_PROMPT = (
    "In one short sentence, summarize the core technical problem, product focus, "
    "or industry challenge this company is solving."
)

FALLBACK_HOOK = "impressed by your engineering team's focus on building scalable and innovative solutions."

EMAIL_TEMPLATE = """Subject: Connecting regarding Software Engineering / AI roles at {company}

Hi {first_name},

I was researching {company} and was really impressed by how you are tackling {ai_hook}.

I am a Computer Science graduate specializing in Cyber Security with a strong foundation in Python, C++, and AI/ML infrastructure. Recently, during my internship at Amazon, I built an optimization-driven data pipeline that improved operational efficiency by 36.81% across 54 stations. I have also developed production-ready computer vision systems (YOLOv11) and RAG-based LLM pipelines. I would love to bring this same results-driven engineering mindset to the team at {company}.

My resume and GitHub are linked below, showcasing my system architecture and my top 0.14% global ranking in TCS CodeVita. Are you currently considering entry-level candidates for any upcoming roles?

Best regards,
Sahil Bhagwat Jadhav
+91 8482976123 | sahiljadhav618@gmail.com
https://www.linkedin.com/in/sahil-jadhav-86b211258/
https://sahxl.netlify.app/"""


def get_gspread_client():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise RuntimeError("GOOGLE_CREDENTIALS environment variable not set")
    
    import json
    creds_dict = json.loads(creds_json)
    # Fix: GitHub Actions secrets may double-escape \n in the private key.
    # Replace literal \\n with real newlines so the PEM parser can read it.
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_sheet_data(client, spreadsheet_id):
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.sheet1
    rows = worksheet.get_all_records()
    return worksheet, rows


def get_pending_rows(rows, limit=50):
    pending = []
    for idx, row in enumerate(rows, start=2):
        if not row.get("Date Sent") or str(row.get("Date Sent")).strip() == "":
            pending.append((idx, row))
            if len(pending) >= limit:
                break
    return pending


def scrape_website(url, timeout=10):
    try:
        if not url or not url.startswith(("http://", "https://")):
            url = "https://" + url
        response = requests.get(url, headers=SCRAPE_HEADERS, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        
        text = soup.get_text(separator=" ", strip=True)
        return " ".join(text.split())[:8000]
    except Exception as e:
        logger.warning(f"Scraping failed for {url}: {e}")
        return None


def generate_ai_hook(scraped_text):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"{GEMINI_PROMPT}\n\nWebsite content:\n{scraped_text[:6000]}"
        response = model.generate_content(prompt)
        
        hook = response.text.strip().strip('"').strip("'")
        if hook and len(hook) > 10:
            return hook
    except Exception as e:
        logger.warning(f"Gemini API failed: {e}")
    
    return FALLBACK_HOOK


def send_email(to_email, subject, body, email_user, email_password):
    msg = MIMEMultipart()
    msg["From"] = email_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)
    return True


def update_sheet_date_sent(worksheet, row_idx, timestamp):
    worksheet.update_cell(row_idx, 6, timestamp)


def build_email_body(first_name, company, ai_hook):
    subject = f"Connecting regarding Software Engineering / AI roles at {company}"
    body = EMAIL_TEMPLATE.format(
        first_name=first_name,
        company=company,
        ai_hook=ai_hook
    )
    return subject, body


def main():
    logger.info("Starting daily cold email outreach...")
    
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    email_user = os.environ.get("EMAIL_USER")
    email_password = os.environ.get("EMAIL_PASSWORD")
    
    if not all([spreadsheet_id, email_user, email_password]):
        raise RuntimeError("Missing required environment variables")
    
    client = get_gspread_client()
    worksheet, rows = get_sheet_data(client, spreadsheet_id)
    
    pending_rows = get_pending_rows(rows, limit=50)
    logger.info(f"Found {len(pending_rows)} contacts to email (max 50)")
    
    sent_count = 0
    failed_count = 0
    
    for row_idx, row in pending_rows:
        first_name = str(row.get("First Name", "")).strip()
        last_name = str(row.get("Last Name", "")).strip()
        email = str(row.get("Email", "")).strip()
        company = str(row.get("Company", "")).strip()
        website = str(row.get("Website", "")).strip()
        
        if not all([first_name, email, company]):
            logger.warning(f"Row {row_idx}: Missing required fields, skipping")
            failed_count += 1
            continue
        
        logger.info(f"Processing {row_idx}: {first_name} {last_name} at {company}")
        
        scraped_text = scrape_website(website) if website else None
        
        if scraped_text:
            ai_hook = generate_ai_hook(scraped_text)
        else:
            ai_hook = FALLBACK_HOOK
            logger.info(f"Using fallback hook for {company}")
        
        subject, body = build_email_body(first_name, company, ai_hook)
        
        try:
            send_email(email, subject, body, email_user, email_password)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_sheet_date_sent(worksheet, row_idx, timestamp)
            logger.info(f"Sent email to {email} at {timestamp}")
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")
            failed_count += 1
        
        if sent_count < 50:
            time.sleep(2)
    
    logger.info(f"Outreach complete. Sent: {sent_count}, Failed: {failed_count}")


if __name__ == "__main__":
    main()