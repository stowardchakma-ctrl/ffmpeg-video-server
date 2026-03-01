from flask import Flask, request, jsonify
import subprocess
import os
import requests
import tempfile

app = Flask(__name__)

def download_file(url, suffix):
    """URL থেকে file download করো"""
    response = requests.get(url)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(response.content)
    tmp.close()
    return tmp.name

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "running"})

@app.route('/create-video', methods=['POST'])
def create_video():
    try:
        data = request.json
        
        image_url = data.get('image_url')
        audio_url = data.get('audio_url')
        
        if not image_url or not audio_url:
            return jsonify({"error": "image_url এবং audio_url দরকার"}), 400

        # File download করো
        image_path = download_file(image_url, '.jpg')
        audio_path = download_file(audio_url, '.mp3')
        output_path = tempfile.mktemp(suffix='.mp4')

        # FFmpeg দিয়ে video বানাও
        command = [
            'ffmpeg',
            '-loop', '1',
            '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            '-vf', 'scale=1080:1080',
            output_path
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500

        # Video file পড়ো এবং return করো
        with open(output_path, 'rb') as f:
            video_data = f.read()

        # Temp files মুছে ফেলো
        os.unlink(image_path)
        os.unlink(audio_path)
        os.unlink(output_path)

        from flask import Response
        return Response(
            video_data,
            mimetype='video/mp4',
            headers={'Content-Disposition': 'attachment; filename=output.mp4'}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
