import httpx
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask import current_app as app

from .forms import SnippetForm, TagForm

main_bp = Blueprint("main", __name__)


def call_api(
    endpoint: str,
    method: str = "GET",
    params: dict | None = None,
    payload: dict | None = None,
) -> dict:
    """Utilty function to call backend API from route logic.

    Args:
        endpoint (str): endpoint to call
        method (str): HTTP call method; can be GET, POST, or DELETE
        params (dict | None): query params to add to endpoint URL
        payload (dict | None): request body content to send with API call

    Returns:
        dict: response from API call
    """

    url = "/".join([app.config["APP_DATA"]["backend_server"], endpoint])

    if method == "GET":
        response = httpx.get(url, params=params)
    elif method == "POST":
        response = httpx.post(url, params=params, json=payload)
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
    form = SnippetForm()
    if form.validate_on_submit():
        data = {
            "title": form.title.data,
            "code": form.code.data,
            "description": form.description.data,
            "language": form.language.data,
            "favorite": form.favorite.data,
        }
        try:
            new_snippet = call_api("snippets", method="POST", payload=data)
            flash("Snippet added successfully!", "success")
            return redirect(url_for("main.view_snippet", snippet_id=new_snippet["id"]))
        except httpx.HTTPStatusError:
            return render_template("snippet_form.html", form=form)

    return render_template("snippet_form.html", form=form)


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


@main_bp.route("/snippet/<int:snippet_id>/tag", methods=["GET", "POST"])
def tag_snippet(snippet_id: int):
    # get current snippet
    try:
        snippet = call_api(f"snippets/{snippet_id}", method="GET")
    except httpx.HTTPStatusError:
        return redirect(url_for("main.index"))

    if request.method == "GET":
        tag_names = ",".join([tag["name"] for tag in snippet.get("tags", [])])
        form = TagForm(tags=tag_names)
        return render_template("tag_form.html", form=form, snippet=snippet)
    if request.method == "POST":
        form = TagForm()
        if form.validate_on_submit():
            current_tags = {tag["name"] for tag in snippet.get("tags", [])}
            input_tags = {
                tag.strip() for tag in form.tags.data.split(",") if tag.strip()
            }
            tags_to_add = list(input_tags - current_tags)
            tags_to_remove = list(current_tags - input_tags)

            try:
                if tags_to_add:
                    call_api(
                        f"snippets/{snippet_id}/tags",
                        method="POST",
                        payload=tags_to_add,
                    )
                if tags_to_remove:
                    params = {"remove": True}
                    call_api(
                        f"snippets/{snippet_id}/tags",
                        method="POST",
                        params=params,
                        payload=tags_to_remove,
                    )
            except httpx.HTTPStatusError:
                return render_template("tag_form.html", form=form, snippet=snippet)

            flash("Tags updated successfully!", "success")
            return redirect(url_for("main.view_snippet", snippet_id=snippet_id))

        return render_template("tag_form.html", form=form, snippet=snippet)
