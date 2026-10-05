from io import BytesIO

from flask import Flask, render_template, request, send_file,session,redirect
import os
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from botocore.exceptions import ClientError
import boto3

secrets_client = boto3.client("secretsmanager", region_name="ap-south-1")
SECRET_NAME = "document-management/app-secrets"

secret_response = secrets_client.get_secret_value(
    SecretId=SECRET_NAME
)

secrets = json.loads(secret_response["SecretString"])

FLASK_SECRET_KEY = secrets["FLASK_SECRET_KEY"]
USER_PASSWORD_HASH = secrets["USER_PASSWORD_HASH"]

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

@app.errorhandler(413)
def request_entity_too_large(error):
    return "File too large. Maximum allowed size is 10 MB.", 413

BUCKET_NAME = "yuvraj-document-management-2026"

ALLOWED_EXTENSIONS = {
    "pdf",
    "docx",
    "txt",
    "jpg",
    "jpeg",
    "png"
}

s3 = boto3.client("s3")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "yuvraj" and check_password_hash(
            USER_PASSWORD_HASH,
            password
        ):
            session["user"] = username
            return redirect("/")

        return "Invalid username or password", 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix="documents/" + session["user"] + "/"
    )

    documents = [
        item["Key"]
        for item in response.get("Contents", [])
    ]

    return render_template(
        "index.html",
        documents=documents
    )


@app.route("/download/<filename>")
def download_file(filename):

    if "user" not in session:
        return "Unauthorized. Please log in.", 401

    try:
        document_key = "documents/" + session["user"] + "/" + filename

        response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=document_key
        )

        file_data = BytesIO(
            response["Body"].read()
        )

        return send_file(
            file_data,
            download_name=filename,
            as_attachment=True
        )

    except ClientError as error:

        error_code = error.response["Error"]["Code"]

        if error_code in ["NoSuchKey", "404"]:
            return "Document not found", 404

        return "An error occurred while downloading", 500


@app.route("/upload", methods=["POST"])
def upload_file():

    if "user" not in session:
        return "Unauthorized. Please log in.", 401

    if "document" not in request.files:
        return "No document selected"

    file = request.files["document"]

    if file.filename == "":
        return "No document selected"

    filename = secure_filename(file.filename)
    
    if "." not in file.filename:
        return "File type not allowed", 400
    
    extension = file.filename.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        return "File type not allowed", 400
   
    try:

        document_key = "documents/" + session["user"] + "/" + filename

        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            document_key
        )
    except ClientError:
        return "Upload failed", 500

    return f"Document uploaded successfully to S3: {filename}"


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )

