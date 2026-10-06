"""Render the Jinja templates to static HTML in docs/ for GitHub Pages (UI only, no data)."""
import shutil
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader, Undefined

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "slis" / "templates"
STATIC = ROOT / "slis" / "static"
OUT = ROOT / "docs"

PAGES = {
    "web.index": "index.html",
    "web.sanctions_manage": "sanctions_manage.html",
    "web.sanctions_upload": "sanctions_upload.html",
    "web.screening_start": "screening_start.html",
    "web.screening_jobs": "screening_jobs.html",
    "web.screening_job_detail": "screening_results.html",
    "web.search_by_name": "search.html",
    "web.data_explorer": "data_explorer.html",
    "web.file_splitter": "file_splitter.html",
    "web.rekon_ai": "rekon_ai.html",
    "lhp.lhp_ai": "lhp_ai.html",
    "web.transaction_batch_upload": "transactions_upload.html",
    "web.wizard_upload": "wizard_step1_upload.html",
    "web.wizard_execute": "wizard_step4_progress.html",
}
EXTRA_TEMPLATES = ["wizard_step2_config.html", "wizard_step3_confirm.html"]


class Blank(Undefined):
    """Missing data renders as empty and behaves like 0 / empty list."""

    __slots__ = ()

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return self

    def __getitem__(self, key):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __str__(self):
        return ""

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0

    def __bool__(self):
        return False

    def __int__(self):
        return 0

    def __float__(self):
        return 0.0

    def __index__(self):
        return 0

    def __format__(self, spec):
        return ""

    def __hash__(self):
        return 0

    def __eq__(self, other):
        return isinstance(other, Undefined)

    def __ne__(self, other):
        return not self.__eq__(other)

    def _num(self, other=None):
        return 0

    __add__ = __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = _num
    __truediv__ = __rtruediv__ = __floordiv__ = __rfloordiv__ = _num
    __mod__ = __rmod__ = __neg__ = __pos__ = __abs__ = _num

    def __lt__(self, other):
        return 0 < other

    def __le__(self, other):
        return 0 <= other

    def __gt__(self, other):
        return 0 > other

    def __ge__(self, other):
        return 0 >= other


def url_for(endpoint, **kwargs):
    if endpoint == "static":
        return "static/" + kwargs["filename"]
    return PAGES.get(endpoint, "#")


def safe_format(value, *args, **kwargs):
    try:
        return str(value) % (kwargs or tuple(0 if isinstance(a, Undefined) else a for a in args))
    except (TypeError, ValueError):
        return ""


def main():
    env = Environment(loader=FileSystemLoader(TEMPLATES), undefined=Blank, autoescape=True)
    env.filters["wib"] = lambda dt: dt
    env.filters["wib_fmt"] = lambda dt, fmt="": "-"
    env.filters["format"] = safe_format

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(STATIC, OUT / "static")
    (OUT / ".nojekyll").write_text("")

    by_file = {filename: endpoint for endpoint, filename in PAGES.items()}
    for filename in [*PAGES.values(), *EXTRA_TEMPLATES]:
        request = SimpleNamespace(
            endpoint=by_file.get(filename, ""),
            form={},
            args={},
            path="",
        )
        html = env.get_template(filename).render(
            url_for=url_for,
            request=request,
            get_flashed_messages=lambda **kw: [],
        )
        (OUT / filename).write_text(html, encoding="utf-8")
        print(f"ok  {filename}  ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
