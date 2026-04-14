import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

import anthropic
import pytz
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ISTANBUL_TZ = pytz.timezone("Europe/Istanbul")

# Telegram supports only: <b>, <i>, <u>, <s>, <a href>, <code>, <pre>
SYSTEM_PROMPT = """You are a technology news curator specializing in AI and large language models.
When asked, you search for and summarize today's most important news about LLM models and AI labs.
Format your response for Telegram using ONLY these HTML tags: <b>, <i>, <a href="URL">.
Structure each story exactly like this (repeat for each story):

<b>Headline here</b>
<i>Source — Date</i>
One to two sentence summary.
<a href="URL">Devamını oku →</a>

Separate stories with a blank line and a line containing only ——
Return ONLY the stories in this format — no intro text, no markdown fences."""

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def fetch_llm_news() -> str:
    """Call the Claude API with web_search tool. Returns Telegram-formatted text."""
    today = datetime.now(ISTANBUL_TZ).strftime("%B %d, %Y")
    client = _get_client()

    messages = [
        {
            "role": "user",
            "content": (
                f"Search for today's ({today}) top 5-10 news stories about large language models "
                "and AI labs. Focus on: Claude, Gemini, ChatGPT, Anthropic, OpenAI, Google DeepMind, "
                "Meta AI, Mistral, and similar. "
                "Format each story for Telegram HTML: bold headline, italic source+date, "
                "1-2 sentence summary, 'Devamını oku →' link. Separate stories with —— on its own line."
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


def _telegram_send(token: str, chat_id: str, text: str) -> None:
    """Send a single Telegram message (max 4096 chars)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")


def send_telegram(text: str, header: str) -> None:
    """Send news digest to Telegram, splitting into chunks if > 4096 chars."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    full_text = f"<b>{header}</b>\n\n{text}"

    # Split at story boundaries if message exceeds Telegram's 4096-char limit
    if len(full_text) <= 4096:
        _telegram_send(token, chat_id, full_text)
        return

    # First chunk: header + as many stories as fit
    chunks = []
    current = f"<b>{header}</b>\n\n"
    for story in text.split("\n——\n"):
        story = story.strip()
        if not story:
            continue
        candidate = current + story + "\n——\n"
        if len(candidate) > 4096 and current.strip():
            chunks.append(current.rstrip("\n——\n"))
            current = story + "\n——\n"
        else:
            current = candidate
    if current.strip():
        chunks.append(current.rstrip("\n——\n"))

    for chunk in chunks:
        _telegram_send(token, chat_id, chunk)


def run_news_routine() -> None:
    """Orchestrate fetch + send. Catches all exceptions so the scheduler never crashes."""
    now = datetime.now(ISTANBUL_TZ)
    slot = "Sabah" if now.hour < 12 else "Aksam"
    header = f"LLM Haber Ozeti — {now.strftime('%d %B %Y')} ({slot})"

    logger.info("LLM haber rutini basliyor: %s", header)
    try:
        news_text = fetch_llm_news()
        send_telegram(news_text, header)
        logger.info("Haber ozeti Telegram'a gonderildi: %s", header)
    except anthropic.APIConnectionError as e:
        logger.error("Anthropic API baglanti hatasi — bu calistirma atlandi: %s", e)
    except anthropic.RateLimitError as e:
        logger.error("Anthropic API rate limit — bu calistirma atlandi: %s", e)
    except anthropic.AuthenticationError as e:
        logger.critical("Anthropic API kimlik dogrulama hatasi — ANTHROPIC_API_KEY kontrol edin: %s", e)
    except anthropic.APIStatusError as e:
        logger.error("Anthropic API hatasi %s: %s — bu calistirma atlandi", e.status_code, e.message)
    except urllib.error.URLError as e:
        logger.error("Telegram API baglanti hatasi — bu calistirma atlandi: %s", e)
    except RuntimeError as e:
        logger.error("Hata: %s — bu calistirma atlandi", e)
    except ValueError as e:
        logger.error("Claude yanit hatasi: %s — bu calistirma atlandi", e)
    except Exception as e:
        logger.exception("Beklenmeyen hata haber rutininde: %s", e)
