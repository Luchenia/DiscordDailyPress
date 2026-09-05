import asyncio
import json
from unittest.mock import Mock

import httpx
import pytest

from app.core.config import Config
from app.services import nvidia_translation_provider as provider_module
from app.services.nvidia_translation_provider import NvidiaTranslationProvider
from app.services.translation_provider import TranslationProviderError


def install_mock_transport(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient
    clients = []

    def client_factory(**kwargs):
        client = real_async_client(transport=transport, **kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr(provider_module.httpx, "AsyncClient", client_factory)
    return clients


def forbid_http_client(monkeypatch):
    client_factory = Mock(side_effect=AssertionError("HTTP client must not be created"))
    monkeypatch.setattr(provider_module.httpx, "AsyncClient", client_factory)
    return client_factory


def test_empty_input_skips_http_request(monkeypatch):
    client_factory = forbid_http_client(monkeypatch)
    provider = NvidiaTranslationProvider(api_key="test-key")

    result = asyncio.run(provider.translate("  \n", "en", "ko"))

    assert result == ""
    client_factory.assert_not_called()


def test_same_language_skips_http_request(monkeypatch):
    client_factory = forbid_http_client(monkeypatch)
    provider = NvidiaTranslationProvider(api_key="test-key")

    result = asyncio.run(provider.translate(" original ", " KO ", "ko"))

    assert result == " original "
    client_factory.assert_not_called()


def test_unknown_source_is_permanent_without_http_request(monkeypatch):
    client_factory = forbid_http_client(monkeypatch)
    provider = NvidiaTranslationProvider(api_key="test-key")

    with pytest.raises(TranslationProviderError) as raised:
        asyncio.run(provider.translate("hello", "unknown", "ko"))

    assert raised.value.retryable is False
    assert raised.value.status_code is None
    client_factory.assert_not_called()


def test_unsupported_source_is_permanent_without_http_request(monkeypatch):
    client_factory = forbid_http_client(monkeypatch)
    provider = NvidiaTranslationProvider(api_key="test-key")

    with pytest.raises(TranslationProviderError) as raised:
        asyncio.run(provider.translate("hello", "xx", "ko"))

    assert raised.value.retryable is False
    client_factory.assert_not_called()


def test_unsupported_target_is_permanent_without_http_request(monkeypatch):
    client_factory = forbid_http_client(monkeypatch)
    provider = NvidiaTranslationProvider(api_key="test-key")

    with pytest.raises(TranslationProviderError) as raised:
        asyncio.run(provider.translate("hello", "en", "xx"))

    assert raised.value.retryable is False
    client_factory.assert_not_called()


def test_en_to_ko_request_and_success_response(monkeypatch):
    observed = {}

    def handler(request):
        authorization = request.headers.get("Authorization", "")
        observed["authorization_valid"] = authorization == "Bearer test-key"
        observed["url"] = str(request.url)
        observed["content_type"] = request.headers.get("Content-Type")
        observed["accept"] = request.headers.get("Accept")
        observed["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "  translated  "}}]},
        )

    clients = install_mock_transport(monkeypatch, handler)
    provider = NvidiaTranslationProvider(api_key="test-key")

    result = asyncio.run(provider.translate("Hello, Chronicle!", "en", "ko"))

    assert result == "translated"
    assert observed["url"] == NvidiaTranslationProvider.ENDPOINT
    assert observed["authorization_valid"] is True
    assert observed["content_type"] == "application/json"
    assert observed["accept"] == "application/json"
    assert observed["payload"] == {
        "model": "nvidia/riva-translate-4b-instruct-v2",
        "messages": [
            {"role": "system", "content": "en-ko"},
            {"role": "user", "content": "Hello, Chronicle!"},
        ],
        "temperature": 0,
        "stream": False,
    }
    assert len(clients) == 1
    assert clients[0].is_closed is True


@pytest.mark.parametrize("content", [None, "", "  \n", 123])
def test_invalid_response_content_is_permanent(monkeypatch, content):
    def handler(request):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}]},
        )

    clients = install_mock_transport(monkeypatch, handler)
    provider = NvidiaTranslationProvider(api_key="test-key")

    with pytest.raises(TranslationProviderError) as raised:
        asyncio.run(provider.translate("hello", "en", "ko"))

    assert raised.value.retryable is False
    assert clients[0].is_closed is True


def test_malformed_response_is_permanent(monkeypatch):
    def handler(request):
        return httpx.Response(200, content=b"not-json")

    install_mock_transport(monkeypatch, handler)
    provider = NvidiaTranslationProvider(api_key="test-key")

    with pytest.raises(TranslationProviderError) as raised:
        asyncio.run(provider.translate("hello", "en", "ko"))

    assert raised.value.retryable is False


@pytest.mark.parametrize(
    ("status_code", "retryable"),
    [
        (202, True),
        (408, True),
        (429, True),
        (500, True),
        (503, True),
        (401, False),
        (403, False),
        (400, False),
        (422, False),
    ],
)
def test_http_status_classification(monkeypatch, status_code, retryable):
    def handler(request):
        return httpx.Response(status_code, json={"error": "failed"})

    clients = install_mock_transport(monkeypatch, handler)
    provider = NvidiaTranslationProvider(api_key="test-key")

    with pytest.raises(TranslationProviderError) as raised:
        asyncio.run(provider.translate("hello", "en", "ko"))

    assert raised.value.retryable is retryable
    assert raised.value.status_code == status_code
    assert clients[0].is_closed is True


def test_httpx_timeout_is_retryable(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("timed out", request=request)

    clients = install_mock_transport(monkeypatch, handler)
    provider = NvidiaTranslationProvider(api_key="test-key")

    with pytest.raises(TranslationProviderError) as raised:
        asyncio.run(provider.translate("hello", "en", "ko"))

    assert raised.value.retryable is True
    assert raised.value.status_code is None
    assert clients[0].is_closed is True


def test_httpx_transport_error_is_retryable(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("connection failed", request=request)

    clients = install_mock_transport(monkeypatch, handler)
    provider = NvidiaTranslationProvider(api_key="test-key")

    with pytest.raises(TranslationProviderError) as raised:
        asyncio.run(provider.translate("hello", "en", "ko"))

    assert raised.value.retryable is True
    assert raised.value.status_code is None
    assert clients[0].is_closed is True


def test_unknown_exception_is_not_converted(monkeypatch):
    error = RuntimeError("unexpected failure")

    def handler(request):
        raise error

    clients = install_mock_transport(monkeypatch, handler)
    provider = NvidiaTranslationProvider(api_key="test-key")

    with pytest.raises(RuntimeError) as raised:
        asyncio.run(provider.translate("hello", "en", "ko"))

    assert raised.value is error
    assert clients[0].is_closed is True


def test_config_nvidia_contract():
    config = Config()

    assert hasattr(config, "nvidia_api_key")
    assert config.nvidia_translation_model == "nvidia/riva-translate-4b-instruct-v2"
