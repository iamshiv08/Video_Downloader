from flask import Flask, render_template, request, send_file, flash, redirect
import yt_dlp
import os
import subprocess

app = Flask(__name__)
app.secret_key = "mysecret"

# Save videos to's Downloads folder
DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("video_url")
        quality = request.form.get("quality")

        if not url:
            flash("⚠️ Please enter a video URL.")
            return redirect("/")

        # Check if it's an Instagram video
        is_instagram = "instagram.com" in url.lower()

        # Choose format depending on platform
        if is_instagram:
            selected_format = "best[ext=mp4]/best"
        else:
            formats = {
                "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
                "Best available": "best",
            }
            selected_format = formats.get(quality, "best")

        # yt-dlp settings
        ydl_opts = {
            "format": selected_format,
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "quiet": True,
        }

        try:
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)

            # Make Instagram reels mobile-friendly
            if is_instagram:
                mobile_path = video_path.replace(".mp4", "_mobile.mp4")

                subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        video_path,
                        "-vf",
                        "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
                        "-c:v",
                        "libx264",
                        "-crf",
                        "23",
                        "-preset",
                        "fast",
                        "-c:a",
                        "aac",
                        "-b:a",
                        "128k",
                        "-movflags",
                        "+faststart",
                        "-y",
                        mobile_path,
                    ]
                )

                video_path = mobile_path

            return send_file(video_path, as_attachment=True)

        except Exception as e:
            flash(f"❌ Failed to download: {e}")
            return redirect("/")

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
