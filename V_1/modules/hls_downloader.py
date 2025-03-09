import subprocess


def download_hls_video(m3u8_url, output_file):
    command = ["ffmpeg", "-i", m3u8_url, "-c", "copy", output_file]
    subprocess.run(command)
