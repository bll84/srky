import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import anthropic
import pytz
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ISTANBUL_TZ = pytz.timezone("Europe/Istanbul")

SYSTEM_PROMPT = """You are a technology news curator specializing in AI and large language models.
When asked, you search for and summarize today's most important news about LLM models and AI labs.
Always respond with a clean HTML digest — no markdown, only valid HTML for email embedding.
Use inline CSS styles only (no <link> or <style> tags, as Gmail strips them).
Structure each story as: <h3> headline, <small> source and date, <p> 1-2 sentence summary, <a> Read more link.
Return ONLY the HTML content body, no markdown fences, no <!DOCTYPE>, no <html> or <body> wrapper tags."""

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def fetch_llm_news() -> str:
    """Call the Claude API with web_search tool. Returns formatted HTML digest."""
    today = datetime.now(ISTANBUL_TZ).strftime("%B %d, %Y")
    client = _get_client()

    messages = [
        {
            "role": "user",
            "content": (
                f"Search for today's ({today}) top 5-10 news stories about large language models "
                "and AI labs. Focus on: Claude, Gemini, ChatGPT, Anthropic, OpenAI, Google DeepMind, "
                "Meta AI, Mistral, and similar. "
                "Format the results as an HTML email body with inline CSS. For each story include: "
                "the headline as <h3 style='margin-bottom:4px;'>, "
                "source and date as <small style='color:#888;'>, "
                "a 1-2 sentence summary as <p style='margin-top:8px;'>, "
                "and a 'Read more →' hyperlink as <a href='URL' style='color:#4a90d9;'>Read more →</a>. "
                "Wrap each story in <div style='margin-bottom:24px;border-bottom:1px solid #eee;padding-bottom:16px;'>. "
                "Return ONLY these story divs — no outer HTML tags, no markdown."
            ),
        }
    ]

    tools = [{"type": "web_search_20260209", "name": "web_search"}]

    max_continuations = 5
    continuations = 0

    while continuations < max_continuations:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    return block.text
            raise ValueError("Claude returned end_turn but no text block found")

        elif response.stop_reason == "pause_turn":
            messages = [
                {"role": "user", "content": messages[0]["content"]},
                {"role": "assistant", "content": response.content},
            ]
            continuations += 1
            continue

        elif response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            continuations += 1
            continue

        else:
            raise ValueError(f"Unexpected stop_reason: {response.stop_reason}")

    raise RuntimeError(f"Exceeded max continuations ({max_continuations}) without end_turn")


def send_email(html_body: str, subject: str) -> None:
    """Send the formatted news digest via Gmail SMTP with TLS."""
    gmail_user = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ["RECIPIENT_EMAIL"]

    full_html = f"""
<html>
<body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;color:#333;padding:20px;">
  <h2 style="border-bottom:2px solid #4a90d9;padding-bottom:8px;color:#222;">{subject}</h2>
  {html_body}
  <p style="color:#aaa;font-size:12px;margin-top:32px;">
    Bu e-posta otomatik olarak LLM News Routine tarafından oluşturulmuştur.
  </p>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = recipient

    plain_text = f"{subject}\n\nLLM Haber Özeti — HTML destekli bir e-posta istemcisinde görüntüleyin."
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(full_html, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(gmail_user, gmail_password)
        smtp.sendmail(gmail_user, recipient, msg.as_string())


def run_news_routine() -> None:
    """Orchestrate fetch + send. Catches all exceptions so the scheduler never crashes."""
    now = datetime.now(ISTANBUL_TZ)
    slot = "Sabah" if now.hour < 12 else "Akşam"
    subject = f"LLM Haber Ozeti — {now.strftime('%d %B %Y')} ({slot})"

    logger.info("LLM haber rutini basliyor: %s", subject)
    try:
        html_body = fetch_llm_news()
        send_email(html_body, subject)
        logger.info("Haber ozeti basariyla gonderildi: %s", subject)
    except anthropic.APIConnectionError as e:
        logger.error("Anthropic API baglanti hatasi — bu calistirma atlandi: %s", e)
    except anthropic.RateLimitError as e:
        logger.error("Anthropic API rate limit — bu calistirma atlandi: %s", e)
    except anthropic.AuthenticationError as e:
        logger.critical("Anthropic API kimlik dogrulama hatasi — ANTHROPIC_API_KEY kontrol edin: %s", e)
    except anthropic.APIStatusError as e:
        logger.error("Anthropic API hatasi %s: %s — bu calistirma atlandi", e.status_code, e.message)
    except smtplib.SMTPAuthenticationError as e:
        logger.critical("Gmail kimlik dogrulama hatasi — GMAIL_APP_PASSWORD kontrol edin: %s", e)
    except smtplib.SMTPException as e:
        logger.error("SMTP hatasi e-posta gonderilirken — bu calistirma atlandi: %s", e)
    except ValueError as e:
        logger.error("Claude yanit hatasi: %s — bu calistirma atlandi", e)
    except RuntimeError as e:
        logger.error("Maksimum devam asimi: %s — bu calistirma atlandi", e)
    except Exception as e:
        logger.exception("Beklenmeyen hata haber rutininde: %s", e)
