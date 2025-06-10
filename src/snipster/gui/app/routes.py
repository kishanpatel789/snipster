import httpx
from flask import Blueprint, flash, render_template
from flask import current_app as app

main_bp = Blueprint("main", __name__)


def call_api(endpoint: str, method: str = "GET", payload: dict | None = None) -> dict:
    url = "/".join([app.config["APP_DATA"]["backend_server"], endpoint])

    if method == "GET":
        response = httpx.get(url, params=payload)
    elif method == "POST":
        response = httpx.post(url, json=payload)

    r_dict = response.json()
    r_status = response.status_code
    if r_status >= 400:
        flash(f"Error {r_status}: {r_dict['detail']}")
    #   r.raise_for_status()

    return r_dict


@main_bp.route("/")
def index():
    snippets = call_api("snippets", method="GET")

    return render_template("index.html", snippets=snippets)


@main_bp.route("/snippet/<int:snippet_id>")
def view_snippet(snippet_id: int):
    pass


@main_bp.route("/snippet/add", methods=["GET", "POST"])
def add_snippet():
    pass
