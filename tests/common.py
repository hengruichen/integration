# pylint: disable=missing-docstring,invalid-name
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
import functools as ft
import json as json_func
import os
from typing import Any, Iterable, Mapping
from unittest.mock import AsyncMock, Mock, patch

from aiohttp import ClientSession, ClientWebSocketResponse
from aiohttp.typedefs import StrOrURL
from awesomeversion import AwesomeVersion
from homeassistant import auth, bootstrap, config_entries, core as ha, config as ha_config
from homeassistant.auth import auth_store, models as auth_models
from homeassistant.const import (
    EVENT_HOMEASSISTANT_CLOSE,
    EVENT_HOMEASSISTANT_STOP,
    __version__ as HAVERSION,
)
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity,
    entity_registry as er,
    issue_registry as ir,
    restore_state as rs,
    storage,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.json import ExtendedJSONEncoder
from homeassistant.setup import async_setup_component
import homeassistant.util.dt as date_util
from homeassistant.util.unit_system import METRIC_SYSTEM
import homeassistant.util.uuid as uuid_util
import pytest
from yarl import URL

from custom_components.hacs.base import HacsBase
from custom_components.hacs.const import DOMAIN
from custom_components.hacs.repositories.base import HacsManifest, HacsRepository
from custom_components.hacs.utils.configuration_schema import TOKEN as CONF_TOKEN
from custom_components.hacs.utils.logger import LOGGER

_LOGGER = LOGGER
TOKEN = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
INSTANCES = []
REQUEST_CONTEXT: ContextVar[pytest.FixtureRequest] = ContextVar("request_context", default=None)

IGNORED_BASE_FILES = set([
        "/config/automations.yaml",
        "/config/configuration.yaml",
        "/config/scenes.yaml",
        "/config/scripts.yaml",
        "/config/secrets.yaml",
    ])


def safe_json_dumps(data: dict | list) -> str:
    return json_func.dumps(
        data,
        indent=4,
        sort_keys=True,
        cls=ExtendedJSONEncoder,
    )


def recursive_remove_key(data: dict[str, Any], to_remove: Iterable[str]) -> dict[str, Any]:
    if not isinstance(data, (Mapping, list)):
        return data

    if isinstance(data, list):
        return [
            recursive_remove_key(val, to_remove)
            for val in sorted(data, key=lambda obj: getattr(obj, "id", 0))
        ]

    copy_data = {**data}
    for key, value in copy_data.items():
        if value is None:
            continue
        if isinstance(value, str) and not value:
            continue
        if key in to_remove:
            copy_data[key] = None
        elif isinstance(value, Mapping):
            copy_data[key] = recursive_remove_key(value, to_remove)
        elif isinstance(value, list):
            copy_data[key] = [
                recursive_remove_key(item, to_remove)
                for item in sorted(value, key=lambda obj: getattr(obj, "id", 0))
            ]
    return copy_data


def fixture(filename, asjson=True):
    """Load a fixture."""
    filename = f"{filename}.json" if "." not in filename else filename
    path = os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        filename.lower().replace("/", "_"),
    )
    try:
        with open(path, encoding="utf-8") as fptr:
            _LOGGER.debug("Loading fixture from %s", path)
            if asjson:
                return json_func.loads(fptr.read())
            return fptr.read()
    except OSError as err:
        raise OSError(f"Missing fixture for {path.split('fixtures/')[1]}") from err


def dummy_repository_base(hacs, repository=None):
    if repository is None:
        repository = HacsRepository(hacs)
        repository.data.full_name = "test/test"
        repository.data.full_name_lower = "test/test"
    repository.hacs = hacs
    repository.hacs.hass = hacs.hass
    rep
# ... [truncated] ...
(fp, encoding="utf-8") as fptr:
                return json_func.loads(fptr.read())

        return MockedResponse(
            url=url,
            read=read,
            json=json,
            headers={
                "X-RateLimit-Limit": "999",
                "X-RateLimit-Remaining": "999",
                "X-RateLimit-Reset": "999",
                "Content-Type": "application/json",
            },
        )


async def client_session_proxy(hass: ha.HomeAssistant) -> ClientSession:
    """Create a mocked client session."""
    base = async_get_clientsession(hass)
    base_request = base._request
    response_mocker = ResponseMocker()

    async def _request(method: str, str_or_url: StrOrURL, *args, **kwargs):
        if str_or_url.startswith("ws://"):
            return await base_request(method, str_or_url, *args, **kwargs)

        if (resp := response_mocker.get(str_or_url, args, kwargs)) is not None:
            LOGGER.info("Using mocked response for %s", str_or_url)
            if resp.exception:
                raise resp.exception
            return resp

        url = URL(str_or_url)
        fixture_file = f"fixtures/proxy/{url.host}{url.path}{'.json' if url.host in ('api.github.com', 'data-v2.hacs.xyz') and not url.path.endswith('.json') else ''}"
        fp = os.path.join(
            os.path.dirname(__file__),
            fixture_file,
        )

        print(f"Using fixture {fp} for request to {url.host}")

        if not os.path.exists(fp):
            raise Exception(f"Missing fixture for proxy/{url.host}{url.path}")

        async def read(**kwargs):
            if url.path.endswith(".zip"):
                with open(fp, mode="rb") as fptr:
                    return fptr.read()
            with open(fp, encoding="utf-8") as fptr:
                return fptr.read().encode("utf-8")

        async def json(**kwargs):
            with open(fp, encoding="utf-8") as fptr:
                return json_func.loads(fptr.read())

        return MockedResponse(
            url=url,
            read=read,
            json=json,
            headers={
                "X-RateLimit-Limit": "999",
                "X-RateLimit-Remaining": "999",
                "X-RateLimit-Reset": "999",
                "Content-Type": "application/json",
            },
        )

    base._request = _request

    return base


def create_config_entry(
    data: dict[str, Any] = None, options: dict[str, Any] = None
) -> MockConfigEntry:
    try:
        # Core 2024.1 added minor_version
        return MockConfigEntry(
            version=1,
            minor_version=0,
            domain=DOMAIN,
            title="",
            data={CONF_TOKEN: TOKEN, **(data or {})},
            source="user",
            options={**(options or {})},
            unique_id="12345",
        )
    except TypeError:
        return MockConfigEntry(
            version=1,
            domain=DOMAIN,
            title="",
            data={CONF_TOKEN: TOKEN, **(data or {})},
            source="user",
            options={**(options or {})},
            unique_id="12345",
        )


async def setup_integration(hass: ha.HomeAssistant, config_entry: MockConfigEntry) -> None:
    mock_session = await client_session_proxy(hass)
    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession", return_value=mock_session
    ):
        hass.data.pop("custom_components", None)
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    hacs: HacsBase = hass.data.get(DOMAIN)
    for repository in hacs.repositories.list_all:
        if repository.data.full_name != "hacs/integration":
            repository.data.installed = False
            repository.data.installed_version = None
            repository.data.installed_commit = None
    assert not hacs.system.disabled


def get_hacs(hass: ha.HomeAssistant) -> HacsBase:
    return hass.data[DOMAIN]

