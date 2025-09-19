import os

from flask import Flask, session, send_from_directory, jsonify, request, redirect, Request, render_template, url_for
from flask_cors import CORS


from task2_2_remon.dropbox_post_remon import DropboxPOSTRemon

app = Flask(__name__, template_folder="templates", static_folder="static", static_url_path="/static")
app.secret_key = "dev-secret-mushfiq"
CORS(app, supports_credentials=True)

dropbox_client = DropboxPOSTRemon()

def set_token(token: str):
    session['access_token'] = token

def get_token():
    return session.get('access_token')

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/auth/start", methods=["GET"])
def auth_start():
    # Use a CSRF state

    url = dropbox_client.get_authorization_url()
    return jsonify({"authorize_url": url})

@app.route("/api/auth/callback", methods=["GET"])
def auth_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    expected_state = session.get("oauth_state")

    if not code:
        return "Missing 'code' in query string.", 400

    try:
        token_data = dropbox_client.post_method_1_get_token(code)
        set_token(token_data['access_token'])

        # If opened in a new tab/popup, notify opener then close; otherwise redirect home.
        html = """
        <!doctype html><meta charset="utf-8"><title>Authorized</title>
        <script>
        (function () {
          try {
            if (window.opener && !window.opener.closed) {
              // Notify the original tab that auth succeeded
              window.opener.postMessage({type:'dropbox-auth', status:'ok'}, window.location.origin);
              window.close();
              return;
            }
          } catch (e) {}
          // Fallback: same-tab flow
          window.location = '/?auth=ok';
        })();
        </script>
        <p>Authorization complete. You can close this tab.</p>
        """
        return html
    except Exception as e:
        return f"Auth error: {e}", 400

@app.route("/api/upload", methods=["POST"])
def upload():
    token = get_token()
    if not token:
        return jsonify({"error": "Not authorized"}), 401

    body = request.get_json(silent=True) or {}
    dropbox_path = body.get("dropbox_path", "/StudyStart_Task_2_2/demo.txt")
    content = body.get("content")  # optional string to upload

    try:
        file_bytes = content.encode("utf-8") if content is not None else None
        result = dropbox_client.post_method_2_upload_file(
            local_file="demo.txt",
            dropbox_path=dropbox_path,
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/create-folder", methods=["POST"])
def create_folder():
    token = get_token()
    if not token:
        return jsonify({"error": "Not authorized"}), 401

    body = request.get_json(silent=True) or {}
    folder_path = body.get("folder_path", "/StudyStart_Task_2_2")

    try:
        result = dropbox_client.post_method_3_create_folder(folder_path)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/list", methods=["GET"])
def list_items():
    # token = get_token()
    # if not token:
    #     return redirect(url_for("home"))

    # inject token for this request
    # dropbox_client.access_token = token

    path = request.args.get("path", "/")
    recursive = request.args.get("recursive", "false").lower() == "true"
    folder_path = "" if path in (None, "", "/") else path

    try:
        data = dropbox_client.list_folder(
            folder_path=folder_path,
            recursive=recursive,
            with_links=False
        )
        return render_template("list.html", path=path, recursive=recursive, entries=data["entries"])
    except Exception as e:
        return f"List error: {e}", 400

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)