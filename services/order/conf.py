import logging
from typing import Any, Tuple, Type

from pydantic import ConfigDict
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)

logger = logging.getLogger(__name__)


class AcceptArrayEnvsSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: Any, value: Any, value_is_complex: bool
    ) -> Any:
        if (
            isinstance(field.annotation, type)
            and issubclass(field.annotation, list)
            and isinstance(value, str)
        ):
            return [x.strip() for x in value.split(",") if x]
        return value


class BaseConfig(BaseSettings):
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (AcceptArrayEnvsSource(settings_cls),)

    model_config = ConfigDict(extra="ignore")  # Ignore extra environment variables


class Settings(BaseConfig):
    service_port: int
    database_url: str
    db_pool_size: int
    db_pool_max_overflow: int
    db_pool_timeout: int
    db_pool_recycle: int
    db_pool_echo: bool


settings = Settings()
