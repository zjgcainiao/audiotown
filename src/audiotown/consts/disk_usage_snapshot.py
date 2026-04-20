
from dataclasses import dataclass, field, asdict
@dataclass(slots=True, frozen=True)
class DiskUsageSnapshot:
    mount_path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    # last_scanned: str  # ISO-8601 UTC timestamp

    @property
    def used_pct_of_total(self) -> float:
        if self.total_bytes <= 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100.0

    @property
    def free_pct_of_total(self) -> float:
        if self.total_bytes <= 0:
            return 0.0
        return (self.free_bytes / self.total_bytes) * 100.0

    def folder_pct_of_total(self, folder_size_bytes: int) -> float:
        if self.total_bytes <= 0:
            return 0.0
        return (folder_size_bytes / self.total_bytes) * 100.0

    def folder_pct_of_free(self, folder_size_bytes: int) -> float:
        if self.free_bytes <= 0:
            return 0.0
        return (folder_size_bytes / self.free_bytes) * 100.0
