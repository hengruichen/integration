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
    repository.data.installed = False
    repository.data.installed_version = None
    repository.data.installed_commit = None
    return repository


def dummy_repository(hacs, repository=None):
    if repository is None:
        repository = dummy_repository_base(hacs)
    repository.data.last_commit = "1234567890"
    repository.data.last_commit_date = "2024-01-01T00:00:00Z"
    repository.data.last_commit_message = "Test commit"
    repository.data.last_commit_author = "Test Author"
    repository.data.last_commit_author_email = "test@example.com"
    repository.data.last_commit_url = "https://github.com/test/test/commit/1234567890"
    repository.data.last_commit_sha = "1234567890"
    repository.data.last_commit_date_utc = "2024-01-01T00:00:00Z"
    repository.data.last_commit_date_local = "2024-01-01T00:00:00Z"
    repository.data.last_commit_date_local_offset = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0
    repository.data.last_commit_date_local_offset_days = 0
    repository.data.last_commit_date_local_offset_months = 0
    repository.data.last_commit_date_local_offset_years = 0
    repository.data.last_commit_date_local_offset_seconds = 0
    repository.data.last_commit_date_local_offset_minutes = 0
    repository.data.last_commit_date_local_offset_hours = 0