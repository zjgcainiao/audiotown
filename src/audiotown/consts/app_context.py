from __future__ import annotations
from pathlib import Path

import click 
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Optional, cast
from audiotown.logger import SessionLogger
from .app_config import AppConfig
from .meta_content import MetaContent
from .ffmpeg_config import FFmpegConfig
from audiotown.services.probe_service import ProbeService
from audiotown.services.scan_service import ScanService
from audiotown.services import ConvertService, PolicyService, CommandBuilderService
from audiotown.video.consts import VideoContainer

@dataclass(slots=True)
class AppContext:
    app_config: AppConfig = field(default_factory=AppConfig)
    start_time: float = 0.0
    run_time: float = 0.0
    ff_config: FFmpegConfig = field(default_factory=FFmpegConfig.create)
    logger: SessionLogger = field(default_factory=SessionLogger)
    dry_run: bool = False
    verbose: bool = False
    meta_content: MetaContent = field(default_factory=MetaContent)
    report_path: Path | None = None
    targeted_container: VideoContainer | None = None


    def get_probe_service(self) -> ProbeService:
        return ProbeService(
            ffprobe_path=self.ff_config.require_ffprobe(),
        )

    def get_scan_service(self) -> ScanService:
        return ScanService(
            probe_service=self.get_probe_service(),
        )
    
    def get_convert_service(self) -> ConvertService:
        ffmpeg_path, ffprobe_path = self.ff_config.require_both()
        return ConvertService(
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            logger=self.logger,
            probe_service=self.get_probe_service(),
            supported_bitrates=self.app_config.supported_bitrates,
            dry_run=self.dry_run,
            verbose=self.verbose,
        )
    
    def get_policy_service(self) -> PolicyService:
        # policy_service = PolicyService()
        return PolicyService()
    
    def get_builder_service(self) -> CommandBuilderService:
        return CommandBuilderService()


    @classmethod
    def get_app_ctx(cls, ctx: click.Context) -> AppContext:
        # We use cast because Click types ctx.obj as Any
        return cast(AppContext, ctx.obj)

    @classmethod
    def ensure_app_ctx(cls, ctx: click.Context) -> AppContext:
        if ctx.obj is None:
             ctx.obj = cls()
            # ctx.obj = AppContext(
            #     start_time=0.0,
            #     run_time=0.0,
            #     app_config=AppConfig(),
            #     ff_config=FFmpegConfig(),
            #     logger=SessionLogger(),
            # )
        return cls.get_app_ctx(ctx)
