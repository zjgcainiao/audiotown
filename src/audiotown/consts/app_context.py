from __future__ import annotations
import click 
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Optional, cast
from audiotown.logger import SessionLogger
from .app_config import AppConfig
from .meta_content import MetaContent
from .ffmpeg_config import FFmpegConfig


@dataclass(slots=True)
class AppContext:
    app_config: AppConfig = field(default_factory=AppConfig)
    start_time: float = 0
    run_time: float = 0
    ff_config: Optional[FFmpegConfig] = field(default_factory=FFmpegConfig)
    logger: SessionLogger = field(default_factory=SessionLogger)
    dry_run: bool = False
    verbose: bool = False
    meta_content: MetaContent = field(default_factory=MetaContent)

    @classmethod
    def get_app_ctx(cls, ctx: click.Context) -> AppContext:
        # We use cast because Click types ctx.obj as Any
        return cast(AppContext, ctx.obj)

    @classmethod
    def ensure_app_ctx(cls, ctx: click.Context) -> AppContext:
        if ctx.obj is None:
            ctx.obj = AppContext(
                start_time=0.0,
                run_time=0,
                app_config=AppConfig(),
                ff_config=None,
                logger=SessionLogger(),
            )
        return cls.get_app_ctx(ctx)
