from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class AivisSettings(BaseModel):
    url: str = Field(
        default="http://localhost:10101",
        description="AivisSpeech Engine URL (Env: AIVIS__URL)",
    )
    default_voice: str = Field(
        default="auto",
        description="Default voice when not specified: 'auto' (first available), speaker name, or style_id (Env: AIVIS__DEFAULT_VOICE)",
    )


class ServerSettings(BaseModel):
    host: str = Field(
        default="0.0.0.0",
        description="Bind host (Env: SERVER__HOST)",
    )
    port: int = Field(
        default=10201,
        description="Bind port (Env: SERVER__PORT)",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode (Env: SERVER__DEBUG)",
    )
    api_key: str | None = Field(
        default=None,
        description="Optional API key for Bearer authentication (Env: SERVER__API_KEY)",
    )


class Settings(BaseSettings):
    aivis: AivisSettings = AivisSettings()
    server: ServerSettings = ServerSettings()

    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__", extra="ignore"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, env_settings, dotenv_settings)


class CLISettings(Settings):
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            CliSettingsSource(settings_cls, cli_parse_args=True),
            env_settings,
            dotenv_settings,
        )


settings = Settings()
