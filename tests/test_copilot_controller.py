import asyncio
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

try:
    import playwright.async_api  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for test environment
    playwright_module = types.ModuleType("playwright")
    async_api_module = types.ModuleType("playwright.async_api")
    async_api_module.async_playwright = lambda: None
    async_api_module.Browser = object
    async_api_module.BrowserContext = object
    async_api_module.Page = object
    async_api_module.TimeoutError = Exception
    sys.modules.setdefault("playwright", playwright_module)
    sys.modules["playwright.async_api"] = async_api_module
    playwright_module.async_api = async_api_module

try:
    import pyotp  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for test environment
    pyotp_module = types.ModuleType("pyotp")

    class _DummyTOTP:
        def __init__(self, secret):
            self.secret = secret

        def now(self):
            return "000000"

    pyotp_module.TOTP = _DummyTOTP
    sys.modules["pyotp"] = pyotp_module

try:
    import keyring  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for test environment
    keyring_module = types.ModuleType("keyring")

    def _dummy_get_password(*args, **kwargs):
        return None

    keyring_module.get_password = _dummy_get_password
    sys.modules["keyring"] = keyring_module

try:
    from dotenv import load_dotenv  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for test environment
    dotenv_module = types.ModuleType("dotenv")

    def _dummy_load_dotenv(*args, **kwargs):
        return False

    dotenv_module.load_dotenv = _dummy_load_dotenv
    sys.modules["dotenv"] = dotenv_module
    load_dotenv = _dummy_load_dotenv

try:
    from pydantic import BaseModel, ConfigDict, Field  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for test environment
    pydantic_module = types.ModuleType("pydantic")

    class _DummyBaseModel:
        model_config = {}

        def __init__(self, **kwargs):
            for name, value in self.__class__.__dict__.items():
                if name.startswith("_") or callable(value):
                    continue
                setattr(self, name, value)
            for key, value in kwargs.items():
                setattr(self, key, value)

    def _dummy_field(default=None, **_kwargs):
        return default

    class _DummyConfigDict(dict):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    pydantic_module.BaseModel = _DummyBaseModel
    pydantic_module.Field = _dummy_field
    pydantic_module.ConfigDict = _DummyConfigDict
    sys.modules["pydantic"] = pydantic_module

import src.automation.copilot_controller as copilot_module
from src.automation.constants import MARKDOWN_INSTRUCTION
from src.automation.copilot_controller import CopilotController


class AsyncSpy:
    def __init__(self, return_value=None) -> None:
        self.return_value = return_value
        self.calls = []

    async def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.return_value

    def assert_called_once_with(self, *args, **kwargs) -> None:
        assert len(self.calls) == 1
        call_args, call_kwargs = self.calls[0]
        assert call_args == args
        assert call_kwargs == kwargs

    def assert_not_called(self) -> None:
        assert not self.calls


class DummyPage:
    def __init__(self) -> None:
        self.goto_urls = []
        self.closed = False

    async def goto(self, url: str) -> None:
        self.goto_urls.append(url)

    async def wait_for_load_state(self, state: str) -> None:
        pass

    async def is_visible(self, selector: str, timeout: int = 0) -> bool:
        return False

    async def close(self) -> None:
        self.closed = True


class DummyContext:
    def __init__(self, page: DummyPage) -> None:
        self.page = page
        self.closed = False
        self.new_page_calls = 0

    async def new_page(self) -> DummyPage:
        self.new_page_calls += 1
        return self.page

    async def close(self) -> None:
        self.closed = True


class DummyBrowser:
    def __init__(self, context: DummyContext) -> None:
        self.context = context
        self.closed = False
        self.storage_args = []

    async def new_context(self, storage_state=None) -> DummyContext:  # type: ignore[override]
        self.storage_args.append(storage_state)
        return self.context

    async def close(self) -> None:
        self.closed = True


class DummyChromium:
    def __init__(self, browser: DummyBrowser) -> None:
        self.browser = browser
        self.launch_args = []

    async def launch(self, headless: bool = True) -> DummyBrowser:
        self.launch_args.append(headless)
        return self.browser


class DummyPlaywright:
    def __init__(self, chromium: DummyChromium) -> None:
        self.chromium = chromium
        self.stopped = False

    async def stop(self) -> None:
        self.stopped = True


class DummyPlaywrightManager:
    def __init__(self, playwright: DummyPlaywright) -> None:
        self.playwright = playwright

    async def start(self) -> DummyPlaywright:
        return self.playwright


def build_playwright_stack(page: DummyPage):
    context = DummyContext(page)
    browser = DummyBrowser(context)
    chromium = DummyChromium(browser)
    playwright = DummyPlaywright(chromium)
    manager = DummyPlaywrightManager(playwright)
    return manager, browser, context, chromium, playwright


async def _stub_logged_in(self, page):
    return True


@pytest.fixture
def make_settings(tmp_path):
    def factory(**overrides):
        storage_state_path = overrides.pop("storage_state_path", tmp_path / "state.json")
        storage_state_path = Path(storage_state_path)
        storage_state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "browser_headless": True,
            "storage_state_path": storage_state_path,
            "copilot_url": "https://copilot.test",
            "username": "user@example.com",
            "password": "super-secret",
            "mfa_secret": None,
            "force_markdown_responses": False,
            "normalize_markdown": True,
        }
        data.update(overrides)
        return SimpleNamespace(**data)

    return factory


def test_start_initialises_playwright_stack(monkeypatch, make_settings):
    async def run():
        settings = make_settings(browser_headless=False)
        page = DummyPage()
        manager, browser, context, chromium, playwright = build_playwright_stack(page)

        monkeypatch.setattr(copilot_module, "get_settings", lambda: settings)
        monkeypatch.setattr(copilot_module, "async_playwright", lambda: manager)

        controller = CopilotController()

        await controller.start()

        assert controller._playwright is playwright
        assert controller.browser is browser
        assert controller.context is context
        assert controller.page is page
        assert chromium.launch_args == [settings.browser_headless]

        await controller.close()

    asyncio.run(run())


def test_ensure_authenticated_requires_start(monkeypatch, make_settings):
    async def run():
        settings = make_settings()
        monkeypatch.setattr(copilot_module, "get_settings", lambda: settings)

        controller = CopilotController()

        with pytest.raises(RuntimeError, match="Controller not started"):
            await controller.ensure_authenticated()

    asyncio.run(run())


def test_ensure_authenticated_refreshes_when_session_invalid(monkeypatch, make_settings):
    async def run():
        settings = make_settings()
        settings.storage_state_path.write_text("{}")

        page = DummyPage()
        manager, browser, context, _, _ = build_playwright_stack(page)

        perform_login_mock = AsyncSpy()

        monkeypatch.setattr(copilot_module, "get_settings", lambda: settings)
        monkeypatch.setattr(copilot_module, "async_playwright", lambda: manager)
        monkeypatch.setattr(copilot_module, "perform_login", perform_login_mock)

        async def _force_not_logged(_: CopilotController, __: DummyPage) -> bool:
            return False

        monkeypatch.setattr(CopilotController, "_check_if_logged_in", _force_not_logged)

        controller = CopilotController()
        await controller.start()

        await controller.ensure_authenticated()

        perform_login_mock.assert_called_once_with(
            controller.context,
            username=settings.username,
            password=settings.password,
            mfa_secret=settings.mfa_secret,
        )

        await controller.close()

    asyncio.run(run())


def test_chat_sends_prompt_and_returns_response(monkeypatch, make_settings):
    async def run():
        settings = make_settings()
        settings.storage_state_path.write_text("{}")

        page = DummyPage()
        manager, browser, context, _, _ = build_playwright_stack(page)

        perform_login_mock = AsyncSpy()
        prepare_mock = AsyncSpy()
        send_mock = AsyncSpy()
        read_mock = AsyncSpy(return_value="generated answer")

        monkeypatch.setattr(copilot_module, "get_settings", lambda: settings)
        monkeypatch.setattr(copilot_module, "async_playwright", lambda: manager)
        monkeypatch.setattr(copilot_module, "perform_login", perform_login_mock)
        monkeypatch.setattr(copilot_module, "prepare_chat_ui", prepare_mock)
        monkeypatch.setattr(copilot_module, "_send_prompt", send_mock)
        monkeypatch.setattr(copilot_module, "_read_response_text", read_mock)
        monkeypatch.setattr(CopilotController, "_check_if_logged_in", _stub_logged_in)

        controller = CopilotController()
        await controller.start()

        prompt = "Summarise the quarterly report"
        result = await controller.chat(prompt)

        assert result == "generated answer"
        prepare_mock.assert_called_once_with(page)
        send_mock.assert_called_once_with(page, prompt)
        read_mock.assert_called_once_with(
            page, exclude_text=prompt, normalise=settings.normalize_markdown
        )
        perform_login_mock.assert_not_called()

        await controller.close()

    asyncio.run(run())


def test_chat_appends_markdown_instruction_when_enabled(monkeypatch, make_settings):
    async def run():
        settings = make_settings(force_markdown_responses=True)
        settings.storage_state_path.write_text("{}")

        page = DummyPage()
        manager, browser, context, _, _ = build_playwright_stack(page)

        prepare_mock = AsyncSpy()
        send_mock = AsyncSpy()
        read_mock = AsyncSpy(return_value="generated answer")

        monkeypatch.setattr(copilot_module, "get_settings", lambda: settings)
        monkeypatch.setattr(copilot_module, "async_playwright", lambda: manager)
        monkeypatch.setattr(copilot_module, "prepare_chat_ui", prepare_mock)
        monkeypatch.setattr(copilot_module, "_send_prompt", send_mock)
        monkeypatch.setattr(copilot_module, "_read_response_text", read_mock)
        monkeypatch.setattr(CopilotController, "_check_if_logged_in", _stub_logged_in)

        controller = CopilotController()
        await controller.start()

        prompt = "Summarise the quarterly report"
        decorated = f"{prompt}\n\n{MARKDOWN_INSTRUCTION}"

        await controller.chat(prompt)

        send_mock.assert_called_once_with(page, decorated)
        read_mock.assert_called_once_with(
            page, exclude_text=decorated, normalise=settings.normalize_markdown
        )

        await controller.close()

    asyncio.run(run())


def test_chat_uses_raw_response_when_normalise_disabled(monkeypatch, make_settings):
    async def run():
        settings = make_settings(force_markdown_responses=True, normalize_markdown=False)
        settings.storage_state_path.write_text("{}")

        page = DummyPage()
        manager, browser, context, _, _ = build_playwright_stack(page)

        prepare_mock = AsyncSpy()
        send_mock = AsyncSpy()
        read_mock = AsyncSpy(return_value="raw answer")

        monkeypatch.setattr(copilot_module, "get_settings", lambda: settings)
        monkeypatch.setattr(copilot_module, "async_playwright", lambda: manager)
        monkeypatch.setattr(copilot_module, "prepare_chat_ui", prepare_mock)
        monkeypatch.setattr(copilot_module, "_send_prompt", send_mock)
        monkeypatch.setattr(copilot_module, "_read_response_text", read_mock)
        monkeypatch.setattr(CopilotController, "_check_if_logged_in", _stub_logged_in)

        controller = CopilotController()
        await controller.start()

        prompt = "Summarise the quarterly report"
        decorated = f"{prompt}\n\n{MARKDOWN_INSTRUCTION}"

        result = await controller.chat(prompt)

        assert result == "raw answer"
        send_mock.assert_called_once_with(page, decorated)
        read_mock.assert_called_once_with(page, exclude_text=decorated, normalise=False)

        await controller.close()

    asyncio.run(run())


def test_ask_with_file_uploads_before_prompt(monkeypatch, make_settings, tmp_path):
    async def run():
        settings = make_settings()
        settings.storage_state_path.write_text("{}")

        page = DummyPage()
        manager, browser, context, _, _ = build_playwright_stack(page)

        perform_login_mock = AsyncSpy()
        prepare_mock = AsyncSpy()
        upload_mock = AsyncSpy()
        send_mock = AsyncSpy()
        read_mock = AsyncSpy(return_value="analysis")

        monkeypatch.setattr(copilot_module, "get_settings", lambda: settings)
        monkeypatch.setattr(copilot_module, "async_playwright", lambda: manager)
        monkeypatch.setattr(copilot_module, "perform_login", perform_login_mock)
        monkeypatch.setattr(copilot_module, "prepare_chat_ui", prepare_mock)
        monkeypatch.setattr(copilot_module, "_upload_file", upload_mock)
        monkeypatch.setattr(copilot_module, "_send_prompt", send_mock)
        monkeypatch.setattr(copilot_module, "_read_response_text", read_mock)
        monkeypatch.setattr(CopilotController, "_check_if_logged_in", _stub_logged_in)

        controller = CopilotController()
        await controller.start()

        file_path = tmp_path / "report.pdf"
        file_path.write_text("dummy content")
        prompt = "Analyse the attached report"

        result = await controller.ask_with_file(file_path, prompt)

        assert result == "analysis"
        prepare_mock.assert_called_once_with(page)
        upload_mock.assert_called_once_with(page, file_path)
        send_mock.assert_called_once_with(page, prompt)
        read_mock.assert_called_once_with(
            page, exclude_text=prompt, normalise=settings.normalize_markdown
        )
        perform_login_mock.assert_not_called()

        await controller.close()

    asyncio.run(run())


def test_download_response_returns_path(monkeypatch, make_settings, tmp_path):
    async def run():
        settings = make_settings()

        page = DummyPage()
        manager, browser, context, _, _ = build_playwright_stack(page)

        download_mock = AsyncSpy(return_value=tmp_path / "copilot-result.txt")

        monkeypatch.setattr(copilot_module, "get_settings", lambda: settings)
        monkeypatch.setattr(copilot_module, "async_playwright", lambda: manager)
        monkeypatch.setattr(copilot_module, "_download_next", download_mock)

        controller = CopilotController()
        await controller.start()

        target_dir = tmp_path / "downloads"
        result_path = await controller.download_response(target_dir, timeout_ms=12345)

        assert result_path == tmp_path / "copilot-result.txt"
        download_mock.assert_called_once_with(page, target_dir, timeout_ms=12345)

        await controller.close()

    asyncio.run(run())


def test_chat_splits_long_prompt_and_instructs_order(monkeypatch, make_settings):
    async def run():
        # Configure small max to force splitting 12000-char prompt into 2 parts
        settings = make_settings(force_markdown_responses=False)
        settings.storage_state_path.write_text("{}")
        # Use 10000 as max per user requirement constant
        settings.max_prompt_chars = 10000

        page = DummyPage()
        manager, browser, context, _, _ = build_playwright_stack(page)

        prepare_mock = AsyncSpy()
        send_mock = AsyncSpy()
        read_mock = AsyncSpy(return_value="ok")

        monkeypatch.setattr(copilot_module, "get_settings", lambda: settings)
        monkeypatch.setattr(copilot_module, "async_playwright", lambda: manager)
        monkeypatch.setattr(copilot_module, "prepare_chat_ui", prepare_mock)
        monkeypatch.setattr(copilot_module, "_send_prompt", send_mock)
        monkeypatch.setattr(copilot_module, "_read_response_text", read_mock)
        monkeypatch.setattr(CopilotController, "_check_if_logged_in", _stub_logged_in)

        controller = CopilotController()
        await controller.start()

        long_prompt = "A" * 12000
        result = await controller.chat(long_prompt)

        assert result == "ok"
        # Expect two sends with 1/2 and 2/2 markers
        assert len(send_mock.calls) == 2
        first_args, _ = send_mock.calls[0]
        second_args, _ = send_mock.calls[1]
        assert "[Part 1/2]" in first_args[1]
        assert "Do not respond yet" in first_args[1]
        assert "[Part 2/2 - Final]" in second_args[1]
        assert "Now process all parts above as a single prompt." in second_args[1]
        # read should exclude the last message
        assert len(read_mock.calls) == 1
        _, read_kwargs = read_mock.calls[0]
        assert read_kwargs.get("exclude_text") == second_args[1]

        await controller.close()

    asyncio.run(run())
