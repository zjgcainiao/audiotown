from enum import StrEnum

# class AppleCompatiblity:
class AppleCompatibility(StrEnum):
    """
    Here are the categories:
        - DIRECT_PLAY: 
            Readable, structurally supported, and already Apple-play compatible.

        - NEEDS_REMUX 
            Readable, structurally supported, streams are Apple-play compatible,
            but container/layout must change.

        - NEEDS_TRANSCODE:
            Readable, structurally supported, but one or more streams are not Apple-play compatible.
        - UNSUPPORTED_STRUCTURE:
            Readable, but the file structure is outside the shapes this policy supports.

        - UNKNOWN
            Not readable enough to classify, or classification is inconclusive.
        """
    DIRECT_PLAY = "direct play"
    NEEDS_REMUX = "needs remux"
    NEEDS_TRANSCODE = "needs transcode"
    UNSUPPORTED_STRUCTURE = "unsupported"
    UNKNOWN = "unknown"