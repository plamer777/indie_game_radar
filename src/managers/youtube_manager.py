import io
from yt_dlp import YoutubeDL
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class YoutubeManager:
    """
    Позволяет скачивать видео в память (BytesIO) с выбором качества.
    Если качество отсутствует — подбирает ближайшее доступное.
    """

    def __init__(self, default_quality: int = 480, fmt: str = "mp4"):
        """
        default_quality: желаемое качество (например 360, 480, 720, 1080, 1440, 2160)
        fmt: mp4/webm
        """
        self._log = get_logger().bind(service="youtube_manager")
        self._default_quality = default_quality
        self._format = fmt
        self._download_complete = False

    def download(self, url: str, quality: int | None = None) -> io.BytesIO:
        """
        Скачивает YouTube-видео в память.
        quality — желаемое качество в пикселях (например 720).
        Если None — используется default.
        """
        self._download_complete = False
        quality = quality or self._default_quality
        buffer = io.BytesIO()

        # Формат запроса с fallback
        # 1) Пытаемся строго height=quality
        # 2) Потом height<=quality (любой чуть ниже)
        # 3) Потом best
        video_format_query = (
            f"bestvideo[height={quality}]+bestaudio/"
            f"bestvideo[height<={quality}]+bestaudio/"
            "best"
        )

        ydl_opts = {
            "format": video_format_query,
            "merge_output_format": self._format,
            "quiet": True,
            "outtmpl": "-",
            "progress_hooks": [lambda d: self._hook(d, buffer)],
        }

        self._download_complete = False

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not self._download_complete:
            raise RuntimeError("Video download failed")

        buffer.seek(0)
        return buffer

    def _hook(self, d: dict, buffer: io.BytesIO) -> None:
        """Получение данных фрагментов."""
        try:
            if d["status"] == "downloading" and d.get("fragment"):
                frag = d["fragment"].get("data")
                if frag:
                    buffer.write(frag)

            if d["status"] == "finished":
                self._download_complete = True
        except Exception as e:
            self._log.error(f'Failed to download fragment: {e}')
