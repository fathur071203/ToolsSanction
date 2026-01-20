from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'sanctions_manage.html'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    parent_template = None
    pass
    parent_template = environment.get_template('base.html', 'sanctions_manage.html')
    for name, parent_block in parent_template.blocks.items():
        context.blocks.setdefault(name, []).append(parent_block)
    yield from parent_template.root_render_func(context)

def block_head(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    _block_vars = {}
    pass
    yield '\n<style>\n  .page-wrap { max-width: 1200px; margin: 0 auto; }\n  .page-title { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; margin-bottom: 1.25rem; }\n  .page-title h1 { font-size: 1.6rem; font-weight: 700; margin: 0; }\n  .meta { color: var(--text-light); font-size: 0.9rem; }\n\n  .cardx { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }\n  .cardx h2 { font-size: 1.1rem; font-weight: 650; margin: 0 0 0.75rem; }\n\n  .small { font-size: 0.85rem; color: var(--text-secondary); }\n\n  .table-wrap { max-height: 520px; overflow: auto; border: 1px solid var(--border); border-radius: 10px; }\n  table { width: 100%; border-collapse: collapse; }\n  th, td { padding: 0.7rem 0.75rem; border-bottom: 1px solid var(--border); vertical-align: top; }\n  thead th { position: sticky; top: 0; background: var(--background); z-index: 1; }\n  .pill { display: inline-block; padding: 0.2rem 0.55rem; border-radius: 999px; background: rgba(14,165,233,0.12); color: var(--primary-accent); font-weight: 600; font-size: 0.78rem; }\n  .source-head { display:flex; align-items: baseline; justify-content: space-between; gap: 1rem; margin-bottom: 0.6rem; }\n  .source-head h2 { margin: 0; }\n  .actions-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem; }\n  .action-panel { border: 1px solid var(--border); border-radius: 10px; padding: 0.9rem; background: rgba(0,0,0,0.02); margin-bottom: 0.75rem; }\n  .inline-edit { margin-top: 0.5rem; }\n  .inline-edit input { font-size: 0.95rem; }\n</style>\n'

def block_scripts(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    _block_vars = {}
    pass
    yield '\n<script>\n  (function () {\n    // Toggle panels (replace dropdown-style <details>)\n    document.querySelectorAll(\'[data-toggle-panel]\').forEach((btn) => {\n      btn.addEventListener(\'click\', () => {\n        const sel = btn.getAttribute(\'data-toggle-panel\');\n        if (!sel) return;\n        const panel = document.querySelector(sel);\n        if (!panel) return;\n        panel.classList.toggle(\'d-none\');\n      });\n    });\n\n    // Toggle inline edit per row\n    document.querySelectorAll(\'[data-toggle-inline-edit]\').forEach((btn) => {\n      btn.addEventListener(\'click\', () => {\n        const sel = btn.getAttribute(\'data-toggle-inline-edit\');\n        if (!sel) return;\n        const box = document.querySelector(sel);\n        if (!box) return;\n        box.classList.toggle(\'d-none\');\n        const input = box.querySelector(\'input[name="new_name"]\');\n        if (input) {\n          input.focus();\n          input.select();\n        }\n      });\n    });\n\n    const forms = document.querySelectorAll(\'form[data-ai-form]\');\n    forms.forEach((form) => {\n      form.addEventListener(\'submit\', () => {\n        const btn = form.querySelector(\'[data-ai-submit]\');\n        if (btn) {\n          btn.disabled = true;\n          btn.textContent = \'Memproses…\';\n        }\n      });\n    });\n  })();\n</script>\n'

def block_content(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    _block_vars = {}
    l_0_json_path = resolve('json_path')
    l_0_sanctions_count = resolve('sanctions_count')
    l_0_url_for = resolve('url_for')
    l_0_q = resolve('q')
    l_0_dttot_token = resolve('dttot_token')
    l_0_active_source = resolve('active_source')
    l_0_per_page = resolve('per_page')
    l_0_sort = resolve('sort')
    l_0_sort_dir = resolve('sort_dir')
    l_0_sid = resolve('sid')
    l_0_filtered_in_source = resolve('filtered_in_source')
    l_0_total_in_source = resolve('total_in_source')
    l_0_per_page_options = resolve('per_page_options')
    l_0_page = resolve('page')
    l_0_prev_page = resolve('prev_page')
    l_0_total_pages = resolve('total_pages')
    l_0_next_page = resolve('next_page')
    l_0_dttot_source = resolve('dttot_source')
    l_0_dttot_preview = resolve('dttot_preview')
    l_0_source_records = resolve('source_records')
    l_0__curr_sort = resolve('_curr_sort')
    l_0__curr_dir = resolve('_curr_dir')
    l_0__next_dir = resolve('_next_dir')
    l_0__arrow_up = resolve('_arrow_up')
    l_0__arrow_dn = resolve('_arrow_dn')
    l_0_sources_summary = resolve('sources_summary')
    try:
        t_1 = environment.filters['length']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'length' found.")
    try:
        t_2 = environment.filters['replace']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'replace' found.")
    try:
        t_3 = environment.tests['defined']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No test named 'defined' found.")
    pass
    yield '\n<div class="page-wrap">\n  <div class="page-title">\n    <div>\n      <h1>Sanctions</h1>\n      <div class="meta">\n        Sumber: <strong>'
    yield escape((undefined(name='json_path') if l_0_json_path is missing else l_0_json_path))
    yield '</strong> · Total: <strong>'
    yield escape((undefined(name='sanctions_count') if l_0_sanctions_count is missing else l_0_sanctions_count))
    yield '</strong>\n      </div>\n    </div>\n    <div class="d-flex gap-2">\n      <a class="btn btn-secondary" href="'
    yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_download', _block_vars=_block_vars))
    yield '">Download JSON</a>\n      <a class="btn btn-secondary" href="'
    yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_upload', _block_vars=_block_vars))
    yield '">Upload / Import</a>\n      <a class="btn btn-primary" href="'
    yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.index', _block_vars=_block_vars))
    yield '">Kembali</a>\n    </div>\n  </div>\n\n  <div class="cardx" style="margin-bottom: 1rem;">\n    <h2>Tambah Source</h2>\n    <p class="small">Tambahkan jenis/source sanctions baru. Source ini akan muncul sebagai grup walau belum ada record.</p>\n\n    <form method="post" class="row g-2 align-items-end">\n      <input type="hidden" name="action" value="add_source">\n      <div class="col-12 col-lg-6">\n        <label class="form-label mb-1">Source</label>\n        <input type="text" class="form-control" name="source" placeholder="Mis. DTTOT/NYDA RI KEPOLISIAN" required>\n      </div>\n      <div class="col-12 col-lg-2 d-grid">\n        <button type="submit" class="btn btn-success">Tambah Source</button>\n      </div>\n    </form>\n  </div>\n\n  <div class="cardx" style="margin-bottom: 1rem;">\n    <h2>Cari Nama</h2>\n    <p class="small">Cari cepat berdasarkan nama (case-insensitive). Kosongkan untuk menampilkan semua.</p>\n\n    '
    if (undefined(name='q') if l_0_q is missing else l_0_q):
        pass
        yield '\n      <div class="small" style="margin-bottom: 0.5rem;">Menampilkan source yang punya hasil untuk: <strong>'
        yield escape((undefined(name='q') if l_0_q is missing else l_0_q))
        yield '</strong></div>\n    '
    yield '\n\n    <form method="get" class="row g-2 align-items-end">\n      '
    if (undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token):
        pass
        yield '\n        <input type="hidden" name="dttot_token" value="'
        yield escape((undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token))
        yield '">\n      '
    yield '\n\n      '
    if (undefined(name='active_source') if l_0_active_source is missing else l_0_active_source):
        pass
        yield '\n        <input type="hidden" name="source" value="'
        yield escape((undefined(name='active_source') if l_0_active_source is missing else l_0_active_source))
        yield '">\n        <input type="hidden" name="per_page" value="'
        yield escape((undefined(name='per_page') if l_0_per_page is missing else l_0_per_page))
        yield '">\n        <input type="hidden" name="page" value="1">\n        <input type="hidden" name="sort" value="'
        yield escape(((undefined(name='sort') if l_0_sort is missing else l_0_sort) or 'order'))
        yield '">\n        <input type="hidden" name="dir" value="'
        yield escape(((undefined(name='sort_dir') if l_0_sort_dir is missing else l_0_sort_dir) or 'asc'))
        yield '">\n      '
    yield '\n\n      <div class="col-12 col-lg-6">\n        <label class="form-label mb-1">Keyword</label>\n        <input type="text" class="form-control" name="q" value="'
    yield escape(((undefined(name='q') if l_0_q is missing else l_0_q) or ''))
    yield '" placeholder="Mis. ahmad / putin / company">\n      </div>\n\n      <div class="col-12 col-lg-2 d-grid">\n        <button type="submit" class="btn btn-primary">Cari</button>\n      </div>\n\n      <div class="col-12 col-lg-2 d-grid">\n        '
    if (undefined(name='active_source') if l_0_active_source is missing else l_0_active_source):
        pass
        yield '\n          <a class="btn btn-secondary" href="'
        yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage', source=(undefined(name='active_source') if l_0_active_source is missing else l_0_active_source), per_page=(undefined(name='per_page') if l_0_per_page is missing else l_0_per_page), page=1, sort=(undefined(name='sort') if l_0_sort is missing else l_0_sort), dir=(undefined(name='sort_dir') if l_0_sort_dir is missing else l_0_sort_dir), dttot_token=(undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token), _block_vars=_block_vars))
        yield '">Reset</a>\n        '
    else:
        pass
        yield '\n          <a class="btn btn-secondary" href="'
        yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage', dttot_token=(undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token), _block_vars=_block_vars))
        yield '">Reset</a>\n        '
    yield '\n      </div>\n    </form>\n  </div>\n\n  '
    if (undefined(name='active_source') if l_0_active_source is missing else l_0_active_source):
        pass
        yield '\n    '
        l_0_sid = t_2(context.eval_ctx, t_2(context.eval_ctx, t_2(context.eval_ctx, (undefined(name='active_source') if l_0_active_source is missing else l_0_active_source), ' ', '_'), '/', '_'), ':', '_')
        _block_vars['sid'] = l_0_sid
        yield '\n    <div class="cardx" style="margin-bottom: 1rem;">\n      <div class="source-head">\n        <div>\n          <h2><span class="pill">'
        yield escape((undefined(name='active_source') if l_0_active_source is missing else l_0_active_source))
        yield '</span></h2>\n          '
        if ((((undefined(name='q') if l_0_q is missing else l_0_q) and t_3((undefined(name='filtered_in_source') if l_0_filtered_in_source is missing else l_0_filtered_in_source))) and t_3((undefined(name='total_in_source') if l_0_total_in_source is missing else l_0_total_in_source))) and ((undefined(name='filtered_in_source') if l_0_filtered_in_source is missing else l_0_filtered_in_source) != (undefined(name='total_in_source') if l_0_total_in_source is missing else l_0_total_in_source))):
            pass
            yield '\n            <div class="small">Hasil: <strong>'
            yield escape((undefined(name='filtered_in_source') if l_0_filtered_in_source is missing else l_0_filtered_in_source))
            yield '</strong> / Total: <strong>'
            yield escape((undefined(name='total_in_source') if l_0_total_in_source is missing else l_0_total_in_source))
            yield '</strong></div>\n          '
        else:
            pass
            yield '\n            <div class="small">Total: <strong>'
            yield escape((undefined(name='total_in_source') if l_0_total_in_source is missing else l_0_total_in_source))
            yield '</strong></div>\n          '
        yield '\n        </div>\n        <div class="d-flex gap-2">\n          <a class="btn btn-secondary btn-sm" href="'
        yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage', q=(undefined(name='q') if l_0_q is missing else l_0_q), dttot_token=(undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token), _block_vars=_block_vars))
        yield '">Kembali ke daftar source</a>\n        </div>\n      </div>\n\n      <div class="row g-2 align-items-end" style="margin-top: 0.25rem;">\n        <div class="col-12 col-lg-4">\n          <form method="get" class="row g-2 align-items-end">\n            <input type="hidden" name="source" value="'
        yield escape((undefined(name='active_source') if l_0_active_source is missing else l_0_active_source))
        yield '">\n            '
        if (undefined(name='q') if l_0_q is missing else l_0_q):
            pass
            yield '<input type="hidden" name="q" value="'
            yield escape((undefined(name='q') if l_0_q is missing else l_0_q))
            yield '">'
        yield '\n            '
        if (undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token):
            pass
            yield '<input type="hidden" name="dttot_token" value="'
            yield escape((undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token))
            yield '">'
        yield '\n            <input type="hidden" name="page" value="1">\n            <input type="hidden" name="sort" value="'
        yield escape(((undefined(name='sort') if l_0_sort is missing else l_0_sort) or 'order'))
        yield '">\n            <input type="hidden" name="dir" value="'
        yield escape(((undefined(name='sort_dir') if l_0_sort_dir is missing else l_0_sort_dir) or 'asc'))
        yield '">\n\n            <div class="col-12">\n              <label class="form-label mb-1">Tampilkan per halaman</label>\n              <select class="form-select" name="per_page" onchange="this.form.submit()">\n                '
        for l_1_opt in (undefined(name='per_page_options') if l_0_per_page_options is missing else l_0_per_page_options):
            _loop_vars = {}
            pass
            yield '\n                  <option value="'
            yield escape(l_1_opt)
            yield '" '
            if ((undefined(name='per_page') if l_0_per_page is missing else l_0_per_page) == l_1_opt):
                pass
                yield 'selected'
            yield '>'
            yield escape(l_1_opt)
            yield '</option>\n                '
        l_1_opt = missing
        yield '\n              </select>\n            </div>\n          </form>\n        </div>\n\n        <div class="col-12 col-lg-8 d-flex justify-content-lg-end align-items-end">\n          <div class="btn-group" role="group" aria-label="Pagination">\n            '
        l_0_prev_page = (1 if ((undefined(name='page') if l_0_page is missing else l_0_page) <= 1) else ((undefined(name='page') if l_0_page is missing else l_0_page) - 1))
        _block_vars['prev_page'] = l_0_prev_page
        yield '\n            '
        l_0_next_page = ((undefined(name='total_pages') if l_0_total_pages is missing else l_0_total_pages) if ((undefined(name='page') if l_0_page is missing else l_0_page) >= (undefined(name='total_pages') if l_0_total_pages is missing else l_0_total_pages)) else ((undefined(name='page') if l_0_page is missing else l_0_page) + 1))
        _block_vars['next_page'] = l_0_next_page
        yield '\n            <a class="btn btn-outline-secondary btn-sm '
        if ((undefined(name='page') if l_0_page is missing else l_0_page) <= 1):
            pass
            yield 'disabled'
        yield '"\n               href="'
        yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage', source=(undefined(name='active_source') if l_0_active_source is missing else l_0_active_source), q=(undefined(name='q') if l_0_q is missing else l_0_q), dttot_token=(undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token), per_page=(undefined(name='per_page') if l_0_per_page is missing else l_0_per_page), page=(undefined(name='prev_page') if l_0_prev_page is missing else l_0_prev_page), sort=(undefined(name='sort') if l_0_sort is missing else l_0_sort), dir=(undefined(name='sort_dir') if l_0_sort_dir is missing else l_0_sort_dir), _block_vars=_block_vars))
        yield '">Prev</a>\n            <span class="btn btn-outline-secondary btn-sm disabled">Page '
        yield escape((undefined(name='page') if l_0_page is missing else l_0_page))
        yield ' / '
        yield escape((undefined(name='total_pages') if l_0_total_pages is missing else l_0_total_pages))
        yield '</span>\n            <a class="btn btn-outline-secondary btn-sm '
        if ((undefined(name='page') if l_0_page is missing else l_0_page) >= (undefined(name='total_pages') if l_0_total_pages is missing else l_0_total_pages)):
            pass
            yield 'disabled'
        yield '"\n               href="'
        yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage', source=(undefined(name='active_source') if l_0_active_source is missing else l_0_active_source), q=(undefined(name='q') if l_0_q is missing else l_0_q), dttot_token=(undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token), per_page=(undefined(name='per_page') if l_0_per_page is missing else l_0_per_page), page=(undefined(name='next_page') if l_0_next_page is missing else l_0_next_page), sort=(undefined(name='sort') if l_0_sort is missing else l_0_sort), dir=(undefined(name='sort_dir') if l_0_sort_dir is missing else l_0_sort_dir), _block_vars=_block_vars))
        yield '">Next</a>\n          </div>\n        </div>\n      </div>\n\n      <div class="actions-row" style="margin-top: 0.75rem;">\n        '
        if ((undefined(name='dttot_source') if l_0_dttot_source is missing else l_0_dttot_source) and ((undefined(name='active_source') if l_0_active_source is missing else l_0_active_source) == (undefined(name='dttot_source') if l_0_dttot_source is missing else l_0_dttot_source))):
            pass
            yield '\n          <button type="button" class="btn btn-outline-primary btn-sm" data-toggle-panel="#dttot-ai-'
            yield escape((undefined(name='sid') if l_0_sid is missing else l_0_sid))
            yield '">AI DTTOT (PDF)</button>\n        '
        yield '\n        <button type="button" class="btn btn-outline-success btn-sm" data-toggle-panel="#add-'
        yield escape((undefined(name='sid') if l_0_sid is missing else l_0_sid))
        yield '">Tambah Data</button>\n        <button type="button" class="btn btn-outline-secondary btn-sm" data-toggle-panel="#upload-'
        yield escape((undefined(name='sid') if l_0_sid is missing else l_0_sid))
        yield '">Upload Excel/CSV</button>\n      </div>\n\n      '
        if ((undefined(name='dttot_source') if l_0_dttot_source is missing else l_0_dttot_source) and ((undefined(name='active_source') if l_0_active_source is missing else l_0_active_source) == (undefined(name='dttot_source') if l_0_dttot_source is missing else l_0_dttot_source))):
            pass
            yield '\n        <div class="action-panel d-none" id="dttot-ai-'
            yield escape((undefined(name='sid') if l_0_sid is missing else l_0_sid))
            yield '">\n          <div class="small">\n            Alur: <strong>Upload PDF</strong> → <strong>AI normalisasi</strong> → <strong>Preview</strong> → <strong>Approve</strong> (baru masuk sanctions.json).\n          </div>\n\n          <form method="post" enctype="multipart/form-data" class="row g-2 align-items-end" style="margin-top: 0.5rem;" data-ai-form>\n            <input type="hidden" name="action" value="dttot_ai_parse">\n            <input type="hidden" name="source" value="'
            yield escape((undefined(name='dttot_source') if l_0_dttot_source is missing else l_0_dttot_source))
            yield '">\n\n            <div class="col-12 col-lg-6">\n              <label class="form-label mb-1">PDF DTTOT</label>\n              <input type="file" class="form-control" name="pdf" accept="application/pdf,.pdf" required>\n              <div class="small" style="margin-top: 0.25rem;">File harus PDF teks (bukan scan gambar).</div>\n            </div>\n\n            <div class="col-12 col-lg-2 d-grid">\n              <button type="submit" class="btn btn-primary" data-ai-submit>Proses AI</button>\n            </div>\n          </form>\n\n          '
            if ((undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token) and (undefined(name='dttot_preview') if l_0_dttot_preview is missing else l_0_dttot_preview)):
                pass
                yield '\n            <div class="small" style="margin-top: 0.75rem;">Preview hasil AI (token: <strong>'
                yield escape((undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token))
                yield '</strong>)</div>\n            <div class="table-wrap" style="max-height: 280px; margin-top: 0.35rem;">\n              <table>\n                <thead>\n                  <tr>\n                    <th style="width: 16%">ID</th>\n                    <th style="width: 34%">Nama</th>\n                    <th style="width: 18%">DOB</th>\n                    <th style="width: 12%">CIT</th>\n                    <th>Remarks</th>\n                  </tr>\n                </thead>\n                <tbody>\n                  '
                for l_1_r in (undefined(name='dttot_preview') if l_0_dttot_preview is missing else l_0_dttot_preview)[:200]:
                    _loop_vars = {}
                    pass
                    yield '\n                  <tr>\n                    <td class="small">'
                    yield escape(((environment.getattr(l_1_r, 'id') or environment.getattr(l_1_r, 'external_id')) or '-'))
                    yield '</td>\n                    <td style="font-weight: 600">'
                    yield escape((environment.getattr(l_1_r, 'name') or '-'))
                    yield '</td>\n                    <td class="small">'
                    yield escape((environment.getattr(l_1_r, 'dob') or '-'))
                    yield '</td>\n                    <td class="small">'
                    yield escape((environment.getattr(l_1_r, 'citizenship') or '-'))
                    yield '</td>\n                    <td class="small">'
                    yield escape((environment.getattr(l_1_r, 'remarks') or '-'))
                    yield '</td>\n                  </tr>\n                  '
                l_1_r = missing
                yield '\n                </tbody>\n              </table>\n            </div>\n\n            <form method="post" class="row g-2 align-items-end" style="margin-top: 0.5rem;">\n              <input type="hidden" name="action" value="dttot_ai_approve">\n              <input type="hidden" name="token" value="'
                yield escape((undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token))
                yield '">\n\n              <div class="col-12 col-lg-4">\n                <label class="form-label mb-1">Mode simpan</label>\n                <select class="form-select" name="mode">\n                  <option value="append" selected>Append (tambah ke data DTTOT)</option>\n                  <option value="replace_source">Replace Source (ganti semua data DTTOT)</option>\n                </select>\n              </div>\n\n              <div class="col-12 col-lg-3 d-grid">\n                <button type="submit" class="btn btn-success">Approve & Simpan</button>\n              </div>\n            </form>\n          '
            yield '\n        </div>\n      '
        yield '\n\n      <div class="action-panel d-none" id="add-'
        yield escape((undefined(name='sid') if l_0_sid is missing else l_0_sid))
        yield '">\n          <form method="post" class="row g-2 align-items-end">\n            <input type="hidden" name="action" value="add_record">\n            <input type="hidden" name="source" value="'
        yield escape((undefined(name='active_source') if l_0_active_source is missing else l_0_active_source))
        yield '">\n\n            <div class="col-12 col-lg-5">\n              <label class="form-label mb-1">Nama</label>\n              <input type="text" class="form-control" name="name" placeholder="Nama individu/entitas" required>\n            </div>\n\n            <div class="col-12 col-lg-3">\n              <label class="form-label mb-1">ID (opsional)</label>\n              <input type="text" class="form-control" name="record_id" placeholder="Auto jika kosong">\n            </div>\n\n            <div class="col-6 col-lg-2">\n              <label class="form-label mb-1">DOB</label>\n              <input type="text" class="form-control" name="dob" placeholder="YYYY-MM-DD">\n            </div>\n\n            <div class="col-6 col-lg-2">\n              <label class="form-label mb-1">CIT</label>\n              <input type="text" class="form-control" name="citizenship" placeholder="ID/US">\n            </div>\n\n            <div class="col-12 col-lg-10">\n              <label class="form-label mb-1">Remarks (opsional)</label>\n              <input type="text" class="form-control" name="remarks" placeholder="Catatan singkat">\n            </div>\n\n            <div class="col-12 col-lg-2 d-grid">\n              <button type="submit" class="btn btn-success">Tambah</button>\n            </div>\n          </form>\n        </div>\n\n        <div class="action-panel d-none" id="upload-'
        yield escape((undefined(name='sid') if l_0_sid is missing else l_0_sid))
        yield '">\n          <form method="post" enctype="multipart/form-data" class="row g-2 align-items-end">\n            <input type="hidden" name="action" value="upload_source_file">\n            <input type="hidden" name="source" value="'
        yield escape((undefined(name='active_source') if l_0_active_source is missing else l_0_active_source))
        yield '">\n\n            <div class="col-12 col-lg-5">\n              <label class="form-label mb-1">File</label>\n              <input type="file" class="form-control" name="file" accept=".csv,.json,application/json,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" required>\n              <div class="small" style="margin-top: 0.25rem;">\n                Format: <strong>CSV/XLSX</strong> (kolom minimal: <strong>name</strong>/<strong>full_name</strong>/<strong>nama</strong>) atau <strong>JSON</strong> (EU/NDJSON juga didukung)\n              </div>\n            </div>\n\n            <div class="col-12 col-lg-3">\n              <label class="form-label mb-1">Mode</label>\n              <select class="form-select" name="mode">\n                <option value="append" selected>Append (tambah)</option>\n                <option value="replace_source">Replace Source (ganti isi source ini)</option>\n              </select>\n            </div>\n\n            <div class="col-12 col-lg-2 d-grid">\n              <button type="submit" class="btn btn-secondary">Upload</button>\n            </div>\n          </form>\n        </div>\n\n        '
        if ((undefined(name='source_records') if l_0_source_records is missing else l_0_source_records) and (t_1((undefined(name='source_records') if l_0_source_records is missing else l_0_source_records)) > 0)):
            pass
            yield '\n        <div class="table-wrap" style="margin-top: 0.75rem;">\n          <table>\n            <thead>\n              '
            l_0__curr_sort = ((undefined(name='sort') if l_0_sort is missing else l_0_sort) or 'order')
            _block_vars['_curr_sort'] = l_0__curr_sort
            yield '\n              '
            l_0__curr_dir = ((undefined(name='sort_dir') if l_0_sort_dir is missing else l_0_sort_dir) or 'asc')
            _block_vars['_curr_dir'] = l_0__curr_dir
            yield '\n              '
            l_0__next_dir = ('desc' if ((undefined(name='_curr_dir') if l_0__curr_dir is missing else l_0__curr_dir) == 'asc') else 'asc')
            _block_vars['_next_dir'] = l_0__next_dir
            yield '\n              '
            l_0__arrow_up = '↑'
            _block_vars['_arrow_up'] = l_0__arrow_up
            yield '\n              '
            l_0__arrow_dn = '↓'
            _block_vars['_arrow_dn'] = l_0__arrow_dn
            yield '\n              <tr>\n                <th style="width: 28%;">\n                  <a href="'
            yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage', source=(undefined(name='active_source') if l_0_active_source is missing else l_0_active_source), q=(undefined(name='q') if l_0_q is missing else l_0_q), dttot_token=(undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token), per_page=(undefined(name='per_page') if l_0_per_page is missing else l_0_per_page), page=1, sort='name', dir=((undefined(name='_next_dir') if l_0__next_dir is missing else l_0__next_dir) if ((undefined(name='_curr_sort') if l_0__curr_sort is missing else l_0__curr_sort) == 'name') else 'asc'), _block_vars=_block_vars))
            yield '" style="text-decoration:none; color:inherit;">\n                    Nama '
            if ((undefined(name='_curr_sort') if l_0__curr_sort is missing else l_0__curr_sort) == 'name'):
                pass
                yield escape(((undefined(name='_arrow_up') if l_0__arrow_up is missing else l_0__arrow_up) if ((undefined(name='_curr_dir') if l_0__curr_dir is missing else l_0__curr_dir) == 'asc') else (undefined(name='_arrow_dn') if l_0__arrow_dn is missing else l_0__arrow_dn)))
            yield '\n                  </a>\n                </th>\n                <th style="width: 18%;">\n                  <a href="'
            yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage', source=(undefined(name='active_source') if l_0_active_source is missing else l_0_active_source), q=(undefined(name='q') if l_0_q is missing else l_0_q), dttot_token=(undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token), per_page=(undefined(name='per_page') if l_0_per_page is missing else l_0_per_page), page=1, sort='id', dir=((undefined(name='_next_dir') if l_0__next_dir is missing else l_0__next_dir) if ((undefined(name='_curr_sort') if l_0__curr_sort is missing else l_0__curr_sort) == 'id') else 'asc'), _block_vars=_block_vars))
            yield '" style="text-decoration:none; color:inherit;">\n                    ID '
            if ((undefined(name='_curr_sort') if l_0__curr_sort is missing else l_0__curr_sort) == 'id'):
                pass
                yield escape(((undefined(name='_arrow_up') if l_0__arrow_up is missing else l_0__arrow_up) if ((undefined(name='_curr_dir') if l_0__curr_dir is missing else l_0__curr_dir) == 'asc') else (undefined(name='_arrow_dn') if l_0__arrow_dn is missing else l_0__arrow_dn)))
            yield '\n                  </a>\n                </th>\n                <th style="width: 14%;">\n                  <a href="'
            yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage', source=(undefined(name='active_source') if l_0_active_source is missing else l_0_active_source), q=(undefined(name='q') if l_0_q is missing else l_0_q), dttot_token=(undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token), per_page=(undefined(name='per_page') if l_0_per_page is missing else l_0_per_page), page=1, sort='dob', dir=((undefined(name='_next_dir') if l_0__next_dir is missing else l_0__next_dir) if ((undefined(name='_curr_sort') if l_0__curr_sort is missing else l_0__curr_sort) == 'dob') else 'asc'), _block_vars=_block_vars))
            yield '" style="text-decoration:none; color:inherit;">\n                    DOB '
            if ((undefined(name='_curr_sort') if l_0__curr_sort is missing else l_0__curr_sort) == 'dob'):
                pass
                yield escape(((undefined(name='_arrow_up') if l_0__arrow_up is missing else l_0__arrow_up) if ((undefined(name='_curr_dir') if l_0__curr_dir is missing else l_0__curr_dir) == 'asc') else (undefined(name='_arrow_dn') if l_0__arrow_dn is missing else l_0__arrow_dn)))
            yield '\n                  </a>\n                </th>\n                <th style="width: 12%;">\n                  <a href="'
            yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage', source=(undefined(name='active_source') if l_0_active_source is missing else l_0_active_source), q=(undefined(name='q') if l_0_q is missing else l_0_q), dttot_token=(undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token), per_page=(undefined(name='per_page') if l_0_per_page is missing else l_0_per_page), page=1, sort='citizenship', dir=((undefined(name='_next_dir') if l_0__next_dir is missing else l_0__next_dir) if ((undefined(name='_curr_sort') if l_0__curr_sort is missing else l_0__curr_sort) == 'citizenship') else 'asc'), _block_vars=_block_vars))
            yield '" style="text-decoration:none; color:inherit;">\n                    Citizenship '
            if ((undefined(name='_curr_sort') if l_0__curr_sort is missing else l_0__curr_sort) == 'citizenship'):
                pass
                yield escape(((undefined(name='_arrow_up') if l_0__arrow_up is missing else l_0__arrow_up) if ((undefined(name='_curr_dir') if l_0__curr_dir is missing else l_0__curr_dir) == 'asc') else (undefined(name='_arrow_dn') if l_0__arrow_dn is missing else l_0__arrow_dn)))
            yield '\n                  </a>\n                </th>\n                <th>\n                  <a href="'
            yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage', source=(undefined(name='active_source') if l_0_active_source is missing else l_0_active_source), q=(undefined(name='q') if l_0_q is missing else l_0_q), dttot_token=(undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token), per_page=(undefined(name='per_page') if l_0_per_page is missing else l_0_per_page), page=1, sort='remarks', dir=((undefined(name='_next_dir') if l_0__next_dir is missing else l_0__next_dir) if ((undefined(name='_curr_sort') if l_0__curr_sort is missing else l_0__curr_sort) == 'remarks') else 'asc'), _block_vars=_block_vars))
            yield '" style="text-decoration:none; color:inherit;">\n                    Remarks '
            if ((undefined(name='_curr_sort') if l_0__curr_sort is missing else l_0__curr_sort) == 'remarks'):
                pass
                yield escape(((undefined(name='_arrow_up') if l_0__arrow_up is missing else l_0__arrow_up) if ((undefined(name='_curr_dir') if l_0__curr_dir is missing else l_0__curr_dir) == 'asc') else (undefined(name='_arrow_dn') if l_0__arrow_dn is missing else l_0__arrow_dn)))
            yield '\n                  </a>\n                </th>\n                <th style="width: 10%;">Aksi</th>\n              </tr>\n            </thead>\n            <tbody>\n              '
            l_1_loop = missing
            for l_1_s, l_1_loop in LoopContext((undefined(name='source_records') if l_0_source_records is missing else l_0_source_records), undefined):
                _loop_vars = {}
                pass
                yield '\n              <tr>\n                <td>\n                  <div style="display:flex; align-items:center; justify-content:space-between; gap:0.5rem;">\n                    <div style="font-weight: 600;">'
                yield escape(environment.getattr(l_1_s, 'name'))
                yield '</div>\n                  </div>\n\n                  '
                if environment.getattr(l_1_s, 'id'):
                    pass
                    yield '\n                  <div class="inline-edit d-none" id="edit-'
                    yield escape((undefined(name='sid') if l_0_sid is missing else l_0_sid))
                    yield '-'
                    yield escape(environment.getattr(l_1_loop, 'index'))
                    yield '">\n                    <form method="post" class="row g-2 align-items-end" style="margin-top: 0.25rem;">\n                      <input type="hidden" name="action" value="update_record_name">\n                      <input type="hidden" name="source" value="'
                    yield escape((undefined(name='active_source') if l_0_active_source is missing else l_0_active_source))
                    yield '">\n                      <input type="hidden" name="record_id" value="'
                    yield escape(environment.getattr(l_1_s, 'id'))
                    yield '">\n\n                      <div class="col-12 col-lg-8">\n                        <input type="text" class="form-control" name="new_name" value="'
                    yield escape(environment.getattr(l_1_s, 'name'))
                    yield '" required>\n                      </div>\n                      <div class="col-12 col-lg-4 d-grid">\n                        <button type="submit" class="btn btn-success">Simpan</button>\n                      </div>\n                    </form>\n                  </div>\n                  '
                yield '\n                </td>\n                <td class="small">'
                yield escape(environment.getattr(l_1_s, 'id'))
                yield '</td>\n                <td class="small">'
                yield escape((environment.getattr(l_1_s, 'dob') or '-'))
                yield '</td>\n                <td class="small">'
                yield escape((environment.getattr(l_1_s, 'citizenship') or '-'))
                yield '</td>\n                <td class="small">'
                yield escape((environment.getattr(l_1_s, 'remarks') or '-'))
                yield '</td>\n                <td>\n                  '
                if environment.getattr(l_1_s, 'id'):
                    pass
                    yield '\n                    <div class="d-flex gap-2" style="flex-wrap:wrap;">\n                      <button type="button" class="btn btn-outline-secondary btn-sm" data-toggle-inline-edit="#edit-'
                    yield escape((undefined(name='sid') if l_0_sid is missing else l_0_sid))
                    yield '-'
                    yield escape(environment.getattr(l_1_loop, 'index'))
                    yield '">Edit</button>\n                      <form method="post" style="display:inline;" onsubmit="return confirm(\'Hapus record ini?\');">\n                        <input type="hidden" name="action" value="delete_record">\n                        <input type="hidden" name="source" value="'
                    yield escape((undefined(name='active_source') if l_0_active_source is missing else l_0_active_source))
                    yield '">\n                        <input type="hidden" name="record_id" value="'
                    yield escape(environment.getattr(l_1_s, 'id'))
                    yield '">\n                        <button type="submit" class="btn btn-outline-danger btn-sm">Hapus</button>\n                      </form>\n                    </div>\n                  '
                else:
                    pass
                    yield '\n                    <span class="small">-</span>\n                  '
                yield '\n                </td>\n              </tr>\n              '
            l_1_loop = l_1_s = missing
            yield '\n            </tbody>\n          </table>\n        </div>\n        '
        else:
            pass
            yield '\n          <div class="small" style="margin-top: 0.75rem;">Tidak ada data untuk source ini'
            if (undefined(name='q') if l_0_q is missing else l_0_q):
                pass
                yield ' (filter: <strong>'
                yield escape((undefined(name='q') if l_0_q is missing else l_0_q))
                yield '</strong>)'
            yield '.</div>\n        '
        yield '\n      </div>\n\n  '
    else:
        pass
        yield '\n    '
        if ((undefined(name='sources_summary') if l_0_sources_summary is missing else l_0_sources_summary) and (t_1((undefined(name='sources_summary') if l_0_sources_summary is missing else l_0_sources_summary)) > 0)):
            pass
            yield '\n      <div class="cardx" style="margin-bottom: 1rem;">\n        <h2>Daftar Source</h2>\n        <p class="small">Klik salah satu source untuk melihat datanya per halaman (pagination).</p>\n\n        <div class="table-wrap" style="max-height: 420px;">\n          <table>\n            <thead>\n              <tr>\n                <th>Source</th>\n                <th style="width: 16%;">Total</th>\n                '
            if (undefined(name='q') if l_0_q is missing else l_0_q):
                pass
                yield '<th style="width: 16%;">Hasil</th>'
            yield '\n                <th style="width: 18%;">Aksi</th>\n              </tr>\n            </thead>\n            <tbody>\n              '
            for l_1_s in (undefined(name='sources_summary') if l_0_sources_summary is missing else l_0_sources_summary):
                _loop_vars = {}
                pass
                yield '\n                <tr>\n                  <td><span class="pill">'
                yield escape(environment.getattr(l_1_s, 'source'))
                yield '</span></td>\n                  <td class="small">'
                yield escape(environment.getattr(l_1_s, 'total_count'))
                yield '</td>\n                  '
                if (undefined(name='q') if l_0_q is missing else l_0_q):
                    pass
                    yield '<td class="small">'
                    yield escape(environment.getattr(l_1_s, 'shown_count'))
                    yield '</td>'
                yield '\n                  <td>\n                    <a class="btn btn-outline-primary btn-sm" href="'
                yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage', source=environment.getattr(l_1_s, 'source'), q=(undefined(name='q') if l_0_q is missing else l_0_q), dttot_token=(undefined(name='dttot_token') if l_0_dttot_token is missing else l_0_dttot_token), per_page=50, page=1, _loop_vars=_loop_vars))
                yield '">Buka</a>\n                  </td>\n                </tr>\n              '
            l_1_s = missing
            yield '\n            </tbody>\n          </table>\n        </div>\n      </div>\n    '
        else:
            pass
            yield '\n      <div class="cardx">\n        <h2>Data kosong</h2>\n        <p class="small">Belum ada data sanctions pada <strong>'
            yield escape((undefined(name='json_path') if l_0_json_path is missing else l_0_json_path))
            yield '</strong>.</p>\n        <a class="btn btn-secondary" href="'
            yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_upload', _block_vars=_block_vars))
            yield '">Upload / Import</a>\n      </div>\n    '
        yield '\n  '
    yield '\n</div>\n'

blocks = {'head': block_head, 'scripts': block_scripts, 'content': block_content}
debug_info = '1=12&3=17&29=27&73=37&79=90&83=94&84=96&85=98&109=100&110=103&114=106&115=109&118=112&119=115&120=117&122=119&123=121&128=124&136=126&137=129&139=134&145=137&146=140&150=143&151=145&152=148&154=155&158=158&165=160&166=162&167=168&169=174&170=176&175=178&176=182&185=192&186=195&187=198&188=202&189=204&190=208&191=212&197=214&198=217&200=220&201=222&204=224&205=227&212=229&225=231&226=234&239=236&241=240&242=242&243=244&244=246&245=248&254=252&272=256&275=258&308=260&311=262&335=264&339=267&340=270&341=273&342=276&343=279&346=282&347=284&351=288&352=290&356=294&357=296&361=300&362=302&366=306&367=308&374=313&378=317&381=319&382=322&385=326&386=328&389=330&398=333&399=335&400=337&401=339&403=341&405=344&408=348&409=350&423=361&428=371&439=374&444=378&446=382&447=384&448=386&450=392&461=399&462=401'