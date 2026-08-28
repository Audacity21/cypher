import random

from yt_dlp import YoutubeDL


class YoutubeMusicResolver:
    """Resolve a request to the first YouTube result without downloading media."""

    def __init__(self, default_playlist_id: str):
        self.default_playlist_id = default_playlist_id

    def resolve(self, query: str | None = None) -> dict:
        target = (
            f"ytsearch1:{query}"
            if query
            else f"https://www.youtube.com/playlist?list={self.default_playlist_id}"
        )
        options = {
            "extract_flat": "in_playlist",
            "quiet": True,
            "no_warnings": True,
        }
        if query:
            options["playlistend"] = 1
        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(target, download=False)

        entries = info.get("entries") or []
        entry = (
            random.SystemRandom().choice(entries)
            if entries and not query
            else entries[0] if entries
            else info
        )
        video_id = entry.get("id") if entry else None
        if not isinstance(video_id, str) or len(video_id) != 11:
            raise RuntimeError("No playable YouTube result was found")

        return {
            "video_id": video_id,
            "title": entry.get("title") or query or "Playlist track",
            "watch_url": f"https://music.youtube.com/watch?v={video_id}",
            "playlist_id": self.default_playlist_id if not query else None,
        }

    def play(self, query: str | None = None) -> dict:
        return self.resolve(query)

    def stop(self) -> dict:
        return {"stopped": True}
