import httpx
from flask import Blueprint, flash, redirect, render_template, url_for
from flask import current_app as app

main_bp = Blueprint("main", __name__)


def call_api(endpoint: str, method: str = "GET", payload: dict | None = None) -> dict:
    url = "/".join([app.config["APP_DATA"]["backend_server"], endpoint])

    if method == "GET":
        response = httpx.get(url, params=payload)
    elif method == "POST":
        response = httpx.post(url, json=payload)
    elif method == "DELETE":
        response = httpx.delete(url)

    r_dict = response.json()
    r_status = response.status_code
    if r_status >= 400:
        flash(f"Error {r_status}: {r_dict['detail']}")
    response.raise_for_status()

    return r_dict


@main_bp.route("/")
def index():
    snippets = call_api("snippets", method="GET")

    return render_template("index.html", snippets=snippets)


@main_bp.route("/snippet/<int:snippet_id>")
def view_snippet(snippet_id: int):
    try:
        snippet = call_api(f"snippets/{snippet_id}", method="GET")
    except httpx.HTTPStatusError:
        return redirect(url_for("main.index"))

    return render_template("snippet.html", snippet=snippet)


@main_bp.route("/snippet/add", methods=["GET", "POST"])
def add_snippet():
    pass


@main_bp.route("/snippet/<int:snippet_id>/toggle-favorite", methods=["POST"])
def toggle_favorite(snippet_id: int):
    try:
        snippet = call_api(f"snippets/{snippet_id}/favorite", method="POST")
        return render_template("snippet.html", snippet=snippet)
    except httpx.HTTPStatusError:
        return redirect(url_for("main.view_snippet", snippet_id=snippet_id))


@main_bp.route("/snippet/<int:snippet_id>/delete", methods=["POST"])
def delete_snippet(snippet_id: int):
    try:
        response = call_api(f"snippets/{snippet_id}", method="DELETE")
        flash(response["detail"], "success")
    except httpx.HTTPStatusError:
        pass
    finally:
        return redirect(url_for("main.index"))
