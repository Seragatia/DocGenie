import yt_dlp
import re
import logging

# ✅ Set up logging
logging.basicConfig(
    filename="extractor.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class VideoExtractor:
    """
    ✅ Extracts metadata (title, duration, formats, etc.) from YouTube and supported platforms.
    """

    def __init__(self, url):
        self.url = url
        self.video_info = None

    def sanitize_filename(self, filename):
        """✅ Cleans filenames by replacing unsafe characters."""
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)  # Replace unsafe characters
        filename = filename.strip().replace(" ", "_")  # Replace spaces
        return filename[:200]  # Enforce filename length limit

    def extract_info(self):
        """
        ✅ Extracts video metadata without downloading the file.
        Returns:
            dict: Extracted metadata including title, duration, available formats, etc.
        """
        try:
            ydl_opts = {"quiet": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.video_info = ydl.extract_info(self.url, download=False)

            if not self.video_info:
                raise ValueError("❌ ERROR: Failed to retrieve video metadata.")

            return {
                "title": self.sanitize_filename(
                    self.video_info.get("title", "Untitled")
                ),
                "id": self.video_info.get("id"),
                "duration": self.video_info.get("duration"),
                "uploader": self.video_info.get("uploader", "Unknown"),
                "upload_date": self.video_info.get("upload_date"),
                "views": self.video_info.get("view_count", 0),
                "like_count": self.video_info.get("like_count", 0),
                "dislike_count": self.video_info.get("dislike_count", 0),
                "formats": self.get_available_formats(),
                "thumbnail": self.video_info.get("thumbnail", None),
            }

        except Exception as e:
            logging.error(f"❌ ERROR: Failed to extract metadata for {self.url} - {e}")
            return {"error": f"Failed to extract metadata: {e}"}

    def get_available_formats(self):
        """
        ✅ Extracts available formats for a given video.
        Returns:
            list: A list of available formats with resolution, codec, and file size.
        """
        if not self.video_info:
            return []

        formats = []
        for fmt in self.video_info.get("formats", []):
            formats.append(
                {
                    "format_id": fmt.get("format_id"),
                    "ext": fmt.get("ext"),
                    "resolution": fmt.get("resolution") or "N/A",
                    "fps": fmt.get("fps"),
                    "filesize": fmt.get("filesize", "Unknown"),
                    "vcodec": fmt.get("vcodec", "N/A"),
                    "acodec": fmt.get("acodec", "N/A"),
                }
            )

        return formats


# ✅ Example Usage
if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=VIDEO_ID"
    extractor = VideoExtractor(url)
    metadata = extractor.extract_info()

    if "error" in metadata:
        print(metadata["error"])
    else:
        print(f"🎬 Title: {metadata['title']}")
        print(f"📅 Upload Date: {metadata['upload_date']}")
        print(f"👤 Uploader: {metadata['uploader']}")
        print(f"👀 Views: {metadata['views']}")
        print(f"👍 Likes: {metadata['like_count']}")
        print(f"🖼️ Thumbnail: {metadata['thumbnail']}")
        print("\n📂 Available Formats:")
        for fmt in metadata["formats"]:
            print(
                f" - {fmt['format_id']}: {fmt['resolution']} ({fmt['ext']}), {fmt['filesize']} bytes"
            )
