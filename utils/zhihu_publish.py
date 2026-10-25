"""Zhihu column publish helpers (Playwright). Settings come from .env via Config."""

import os
import re
from typing import List

import markdown
from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from utils.common import conf
from utils.path_utils import get_file_path

COOKIE_DIR = get_file_path("cookie")
STATE_FILE = os.path.join(COOKIE_DIR, conf.require("ZHIHU_STATE_FILENAME"))
SCREENSHOT_DIR = get_file_path("logs")
SCREENSHOT_NAME = conf.require("ZHIHU_SCREENSHOT_FILENAME")

SIGNIN_URL = conf.require("ZHIHU_SIGNIN_URL")
WRITE_URL = conf.require("ZHIHU_WRITE_URL")
COOKIE_URL = conf.require("ZHIHU_COOKIE_URL")
LOGIN_COOKIE = conf.require("ZHIHU_LOGIN_COOKIE")
LOGIN_TIMEOUT_MS = conf.require_int("ZHIHU_LOGIN_TIMEOUT_MS")
HEADLESS = os.getenv("ZHIHU_HEADLESS", "false").lower() == "true"
MAX_TOPICS = conf.require_int("ZHIHU_MAX_TOPICS")
SIGNIN_MARKER = conf.require("ZHIHU_SIGNIN_URL_MARKER")
GOTO_WAIT_UNTIL = conf.require("ZHIHU_GOTO_WAIT_UNTIL")
TOPIC_SPLIT_RE = re.compile(conf.require("ZHIHU_TOPIC_SPLIT_REGEX"))
MARKDOWN_EXTENSIONS = conf.require_json("ZHIHU_MARKDOWN_EXTENSIONS")
VIEWPORT = conf.require_json("ZHIHU_VIEWPORT")
TIMEOUTS = conf.require_json("ZHIHU_TIMEOUTS")
SEL = conf.require_json("ZHIHU_SELECTORS")
PASTE_JS = conf.require("ZHIHU_PASTE_JS")
UPLOAD_WAIT_JS = conf.require("ZHIHU_UPLOAD_WAIT_JS")


def _t(key: str) -> int:
    return int(TIMEOUTS[key])


def _phone_modal(page: Page):
    return page.locator(".Modal").filter(has_text=SEL["phone_modal_text"])


def phone_modal_visible(page: Page) -> bool:
    try:
        modal = _phone_modal(page)
        return bool(modal.count() and modal.first.is_visible())
    except Exception:
        return False


def dismiss_blocking_modals(page: Page) -> None:
    """Close phone-binding overlays without closing the image-upload modal (edit/upload steps only)."""
    try:
        modal = _phone_modal(page)
        if modal.count() and modal.first.is_visible():
            modal.first.locator(SEL["modal_close"]).first.click(timeout=_t("modal_close_ms"))
            page.wait_for_timeout(_t("after_modal_ms"))
    except Exception:
        pass


def wait_for_phone_bind(page: Page, context: BrowserContext | None = None) -> None:
    """Publishing requires a bound phone; wait for the user to finish SMS verification."""
    if not phone_modal_visible(page):
        return

    print("=" * 60)
    print("Zhihu requires binding a phone number before publish.")
    print("In the browser window that is open:")
    print("  1. Enter your phone number")
    print("  2. Send and enter the SMS verification code")
    print("  3. Click 确认 — this script continues automatically after the modal closes")
    print(f"Waiting up to {LOGIN_TIMEOUT_MS // 60000} minutes...")
    print("=" * 60)

    waited = 0
    while phone_modal_visible(page):
        if waited >= LOGIN_TIMEOUT_MS:
            raise TimeoutError("Phone binding timed out; bind a phone on Zhihu and run again")
        page.wait_for_timeout(_t("login_poll_ms"))
        waited += _t("login_poll_ms")

    page.wait_for_timeout(_t("post_login_settle_ms"))
    if context is not None:
        os.makedirs(COOKIE_DIR, exist_ok=True)
        context.storage_state(path=STATE_FILE)
        print(f"Phone binding done, session saved to: {STATE_FILE}")


def is_logged_in(context: BrowserContext) -> bool:
    return any(c["name"] == LOGIN_COOKIE for c in context.cookies(COOKIE_URL))


def _launch_browser(playwright: Playwright, headless: bool):
    # Prefer installed Chrome to reduce Zhihu anti-bot blocks (SMS / upload)
    try:
        return playwright.chromium.launch(headless=headless, channel="chrome")
    except Exception:
        return playwright.chromium.launch(headless=headless)


def login_and_save_state(playwright: Playwright) -> None:
    browser = _launch_browser(playwright, headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(SIGNIN_URL)

    print("=" * 60)
    print("Zhihu login required. In the browser window that just opened:")
    print("  1. Scan the QR code with the Zhihu app, or log in with phone/password")
    print("  2. Finish any captcha or SMS verification")
    print("  3. Wait - the window closes by itself once login succeeds")
    print(f"Waiting up to {LOGIN_TIMEOUT_MS // 60000} minutes...")
    print("=" * 60)

    waited = 0
    while not is_logged_in(context):
        if waited >= LOGIN_TIMEOUT_MS:
            browser.close()
            raise TimeoutError("Zhihu login timed out, please run again and log in within 5 minutes")
        page.wait_for_timeout(_t("login_poll_ms"))
        waited += _t("login_poll_ms")

    page.wait_for_timeout(_t("post_login_settle_ms"))
    os.makedirs(COOKIE_DIR, exist_ok=True)
    context.storage_state(path=STATE_FILE)
    browser.close()
    print(f"Login succeeded, session saved to: {STATE_FILE}")


def open_write_page(playwright: Playwright):
    for attempt in range(2):
        if not os.path.isfile(STATE_FILE):
            login_and_save_state(playwright)

        browser = _launch_browser(playwright, headless=HEADLESS)
        context = browser.new_context(storage_state=STATE_FILE, viewport=VIEWPORT)
        page = context.new_page()
        page.goto(WRITE_URL, wait_until=GOTO_WAIT_UNTIL)
        page.wait_for_timeout(_t("after_goto_ms"))
        dismiss_blocking_modals(page)

        if SIGNIN_MARKER not in page.url and is_logged_in(context):
            return browser, page

        browser.close()
        print("Saved Zhihu session has expired, logging in again")
        os.remove(STATE_FILE)

    raise RuntimeError("Could not log in to Zhihu")


def fill_title(page: Page, title: str) -> None:
    title_box = page.locator(SEL["title"]).first
    title_box.wait_for(timeout=_t("title_wait_ms"))
    title_box.fill(title[:100])


def fill_content(page: Page, content_markdown: str) -> None:
    editor = page.locator(SEL["editor"]).first
    editor.wait_for(timeout=_t("editor_wait_ms"))
    editor.click()

    html = markdown.markdown(content_markdown, extensions=MARKDOWN_EXTENSIONS)
    page.evaluate(PASTE_JS, [html, content_markdown])
    page.wait_for_timeout(_t("after_paste_ms"))

    if not editor.inner_text().strip():
        editor.click()
        page.keyboard.insert_text(content_markdown)


def _editor_image_count(page: Page) -> int:
    return page.locator(f"{SEL['editor']} img").count()


def _click_insert_images(page: Page) -> None:
    insert_name = SEL["insert_image_button_name"]
    dismiss_blocking_modals(page)
    try:
        page.get_by_role("button", name=insert_name).click(timeout=10000)
    except Exception:
        page.evaluate(
            """(name) => {
                const btn = [...document.querySelectorAll('button')]
                    .find(b => b.innerText.trim() === name && !b.disabled);
                if (!btn) throw new Error('insert button not found');
                btn.click();
            }""",
            insert_name,
        )
    page.wait_for_timeout(_t("after_insert_ms"))
    dismiss_blocking_modals(page)


def upload_images(page: Page, image_path_list: List[str]) -> None:
    if not image_path_list:
        return

    needed = len(image_path_list)
    if _editor_image_count(page) >= needed:
        print(f"Editor already has {_editor_image_count(page)} images, skipping upload")
        return

    dismiss_blocking_modals(page)
    editor = page.locator(SEL["editor"]).first
    editor.click()
    page.keyboard.press("ControlOrMeta+End")
    page.keyboard.press("Enter")

    page.locator(SEL["image_button"]).first.click()
    file_input = page.locator(SEL["image_file_input"]).first
    file_input.wait_for(state="attached", timeout=_t("file_input_ms"))
    file_input.set_input_files(image_path_list)

    # Poll while dismissing phone modal; accept "enough uploaded" or enabled insert button
    waited = 0
    timeout_ms = _t("upload_wait_ms")
    ready = False
    while waited < timeout_ms:
        dismiss_blocking_modals(page)
        try:
            if page.evaluate(UPLOAD_WAIT_JS, needed):
                ready = True
                break
        except Exception:
            pass
        # Fallback: insert button enabled and at least one uploaded thumbnail
        try:
            state = page.evaluate(
                """(name) => {
                    const modal = document.querySelector('.Modal-content');
                    const btn = [...document.querySelectorAll('button')]
                        .find(b => b.innerText.trim() === name && !b.disabled);
                    const m = modal && modal.innerText.match(/已上传\\s*(\\d+)\\s*张/);
                    return {hasBtn: !!btn, count: m ? Number(m[1]) : 0, modalText: modal ? modal.innerText.slice(0,120) : null};
                }""",
                SEL["insert_image_button_name"],
            )
            if state.get("hasBtn") and state.get("count", 0) >= needed:
                print(f"Upload ready via fallback: {state}")
                ready = True
                break
        except Exception:
            pass
        page.wait_for_timeout(_t("login_poll_ms"))
        waited += _t("login_poll_ms")

    if not ready:
        # Last chance: if images already landed in editor, continue
        if _editor_image_count(page) >= 1:
            print("Upload wait timed out but editor has images; continuing")
            dismiss_blocking_modals(page)
            return
        raise TimeoutError("Image upload did not finish in time")

    _click_insert_images(page)


def add_topics(page: Page, site: str) -> None:
    topics = [t.strip() for t in TOPIC_SPLIT_RE.split(site) if t.strip()][:MAX_TOPICS]
    topic_btn_re = re.compile(SEL["topic_button_regex"])
    for topic in topics:
        try:
            dismiss_blocking_modals(page)
            # Prefer legacy "添加话题"; otherwise open the 文章话题 control in 发布设置
            if page.get_by_role("button", name=topic_btn_re).count():
                page.get_by_role("button", name=topic_btn_re).first.click(timeout=_t("topic_click_ms"))
            elif page.get_by_text("文章话题").count():
                page.get_by_text("文章话题").first.click(timeout=3000)
                plus = page.locator("text=文章话题").locator("..").locator("button, [role='button']")
                if plus.count():
                    plus.first.click(timeout=3000)

            search = page.locator("input[placeholder*='话题'], input[placeholder*='搜索话题']")
            search.first.wait_for(state="visible", timeout=_t("topic_click_ms"))
            search.first.fill(topic)
            page.wait_for_timeout(_t("topic_suggest_wait_ms"))
            suggestion = page.locator(SEL["topic_suggestion"]).first
            suggestion.click(timeout=_t("topic_suggest_click_ms"))
            page.wait_for_timeout(_t("after_topic_ms"))
            print(f"Added topic: {topic}")
        except Exception as e:
            print(f"Could not add topic '{topic}': {e}")
            page.keyboard.press("Escape")


def _is_published_article_url(url: str) -> bool:
    """Draft/edit URLs look like /p/<id>/edit; published ones are /p/<id> optionally with query."""
    if "/edit" in url or "/write" in url:
        return False
    return bool(re.search(r"zhuanlan\.zhihu\.com/p/\d+(?:[?#]|$)", url))


def click_publish(page: Page, context: BrowserContext | None = None) -> str:
    deadline_ms = _t("publish_url_ms")

    for attempt in range(3):
        wait_for_phone_bind(page, context)
        before = page.url
        page.get_by_role("button", name=SEL["publish_button_name"], exact=True).last.click()
        try:
            # Must leave /write or /edit — matching draft /p/<id>/edit is NOT success
            page.wait_for_function(
                """() => {
                    const u = location.href;
                    return !u.includes('/edit') && !u.includes('/write')
                        && /zhuanlan\\.zhihu\\.com\\/p\\/\\d+/.test(u);
                }""",
                timeout=max(deadline_ms // 3, 20000),
            )
            page.wait_for_timeout(1500)
            url = page.url
            if not _is_published_article_url(url):
                raise RuntimeError(f"Publish did not reach article URL (still at {url})")
            if context is not None:
                os.makedirs(COOKIE_DIR, exist_ok=True)
                context.storage_state(path=STATE_FILE)
            # Normalize to public article URL without edit/query noise when possible
            m = re.search(r"(https://zhuanlan\.zhihu\.com/p/\d+)", url)
            return m.group(1) if m else url
        except Exception as e:
            print(f"Publish attempt {attempt + 1} from {before}: {e}")
            if phone_modal_visible(page):
                print("Publish blocked by phone binding modal; waiting for you to finish...")
                continue
            if attempt == 2:
                raise
            page.wait_for_timeout(2000)

    raise RuntimeError("Could not publish Zhihu article")


def publish_to_zhihu(
    title: str,
    content: str,
    site: str,
    image_path_list: List[str],
    dry_run: bool = False,
) -> str:
    with sync_playwright() as playwright:
        # Publishing may need interactive phone binding, so force a visible browser
        browser, page = open_write_page(playwright)
        context = page.context
        try:
            fill_title(page, title)
            fill_content(page, content)
            upload_images(page, image_path_list)
            add_topics(page, site)

            if dry_run:
                print("Dry run: article filled in but not published. Close the browser window to finish.")
                page.wait_for_event("close", timeout=0)
                return page.url
            return click_publish(page, context)
        except Exception:
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            screenshot = os.path.join(SCREENSHOT_DIR, SCREENSHOT_NAME)
            page.screenshot(path=screenshot, full_page=True)
            print(f"Publish failed, screenshot saved to: {screenshot}")
            raise
        finally:
            browser.close()
