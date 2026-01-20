from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'base.html'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_url_for = resolve('url_for')
    l_0_get_flashed_messages = resolve('get_flashed_messages')
    pass
    yield '<!doctype html>\n<html lang="en">\n<head>\n  <meta charset="utf-8">\n  <title>SLIS - Sanction List Screening System</title>\n  <meta name="viewport" content="width=device-width, initial-scale=1">\n\n  <!-- Bootstrap 5 CDN -->\n  <link\n    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"\n    rel="stylesheet"\n    integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN"\n    crossorigin="anonymous"\n  >\n\n  <!-- Google Fonts for modern typography -->\n  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">\n\n  <style>\n    /* Complete redesign: modern color system, typography, and layout */\n    :root {\n      --primary: #0f172a;\n      --primary-light: #1e293b;\n      --primary-accent: #0ea5e9;\n      --secondary: #6366f1;\n      --success: #10b981;\n      --warning: #f59e0b;\n      --danger: #ef4444;\n      --background: #f8fafc;\n      --surface: #ffffff;\n      --border: #e2e8f0;\n      --text-primary: #0f172a;\n      --text-secondary: #64748b;\n      --text-light: #94a3b8;\n    }\n\n    * {\n      font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif;\n    }\n\n    body {\n      background-color: var(--background);\n      color: var(--text-primary);\n      font-size: 14px;\n      line-height: 1.6;\n    }\n\n    /* Navbar Styling */\n    .navbar {\n      background: #005596;\n      padding: 1rem 0;\n      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);\n      border-bottom: 1px solid rgba(14, 165, 233, 0.1);\n    }\n\n    .navbar-brand {\n      font-weight: 700;\n      font-size: 1.5rem;\n      color: var(--primary-accent) !important;\n      letter-spacing: -0.5px;\n      display: flex;\n      align-items: center;\n      gap: 0.65rem;\n    }\n\n    .navbar-logo {\n      width: 50;\n      height: 50px;\n      object-fit: contain;\n    }\n\n    .nav-link {\n      color: rgba(255, 255, 255, 0.8) !important;\n      font-weight: 500;\n      font-size: 0.95rem;\n      padding: 0.5rem 1rem !important;\n      border-radius: 6px;\n      transition: all 0.2s ease;\n    }\n\n    .nav-link:hover {\n      background-color: rgba(14, 165, 233, 0.15);\n      color: var(--primary-accent) !important;\n    }\n\n    .nav-link.active {\n      background-color: rgba(14, 165, 233, 0.2);\n      color: var(--primary-accent) !important;\n    }\n\n    /* Main Container */\n    main.container {\n      max-width: 1200px;\n      padding: 2rem;\n    }\n\n    /* Alerts */\n    .alert {\n      border-radius: 8px;\n      border: none;\n      font-size: 0.95rem;\n      margin-bottom: 1.5rem;\n      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);\n    }\n\n    .alert-success {\n      background-color: #ecfdf5;\n      color: #065f46;\n    }\n\n    .alert-danger {\n      background-color: #fef2f2;\n      color: #7f1d1d;\n    }\n\n    .alert-warning {\n      background-color: #fffbeb;\n      color: #78350f;\n    }\n\n    .alert-info {\n      background-color: #f0f9ff;\n      color: #0c2d6b;\n    }\n\n    /* Button Styles */\n    .btn {\n      border-radius: 6px;\n      font-weight: 500;\n      font-size: 0.95rem;\n      padding: 0.6rem 1.2rem;\n      border: none;\n      transition: all 0.2s ease;\n      cursor: pointer;\n    }\n\n    .btn-primary {\n      background-color: var(--primary-accent);\n      color: white;\n    }\n\n    .btn-primary:hover {\n      background-color: #0284c7;\n      transform: translateY(-2px);\n      box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);\n    }\n\n    .btn-secondary {\n      background-color: var(--secondary);\n      color: white;\n    }\n\n    .btn-secondary:hover {\n      background-color: #4f46e5;\n      transform: translateY(-2px);\n      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);\n    }\n\n    .btn-success {\n      background-color: var(--success);\n      color: white;\n    }\n\n    .btn-success:hover {\n      background-color: #059669;\n      transform: translateY(-2px);\n      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);\n    }\n\n    .btn-warning {\n      background-color: var(--warning);\n      color: white;\n    }\n\n    .btn-warning:hover {\n      background-color: #d97706;\n      transform: translateY(-2px);\n      box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);\n    }\n\n    .btn-lg {\n      padding: 0.75rem 1.5rem;\n      font-size: 1rem;\n    }\n\n    .btn-link {\n      color: var(--primary-accent);\n      text-decoration: none;\n      font-weight: 500;\n    }\n\n    .btn-link:hover {\n      color: #0284c7;\n      text-decoration: underline;\n    }\n\n    /* Card Styles */\n    .card {\n      border: 1px solid var(--border);\n      border-radius: 8px;\n      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);\n      background-color: var(--surface);\n      transition: all 0.2s ease;\n    }\n\n    .card:hover {\n      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);\n      transform: translateY(-2px);\n    }\n\n    .card-header {\n      background-color: var(--background);\n      border-bottom: 1px solid var(--border);\n      font-weight: 600;\n      color: var(--text-primary);\n    }\n\n    .card-title {\n      font-weight: 600;\n      color: var(--text-primary);\n      margin-bottom: 0.5rem;\n    }\n\n    .card-text {\n      color: var(--text-secondary);\n      font-size: 0.9rem;\n    }\n\n    /* Form Elements */\n    .form-label {\n      font-weight: 500;\n      color: var(--text-primary);\n      margin-bottom: 0.5rem;\n    }\n\n    .form-control, .form-select {\n      border: 1px solid var(--border);\n      border-radius: 6px;\n      padding: 0.625rem 0.875rem;\n      font-size: 0.95rem;\n      transition: all 0.2s ease;\n      background-color: var(--surface);\n      color: var(--text-primary);\n    }\n\n    .form-control:focus, .form-select:focus {\n      border-color: var(--primary-accent);\n      box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);\n      outline: none;\n    }\n\n    .form-text {\n      color: var(--text-light);\n      font-size: 0.85rem;\n      margin-top: 0.25rem;\n    }\n\n    /* Badge Styles */\n    .badge {\n      border-radius: 20px;\n      padding: 0.4rem 0.8rem;\n      font-size: 0.8rem;\n      font-weight: 600;\n    }\n\n    .bg-success {\n      background-color: var(--success) !important;\n    }\n\n    .bg-warning {\n      background-color: var(--warning) !important;\n    }\n\n    .bg-danger {\n      background-color: var(--danger) !important;\n    }\n\n    /* Table Styles */\n    .table {\n      border-collapse: collapse;\n      font-size: 0.9rem;\n    }\n\n    .table thead {\n      background-color: var(--background);\n      border-bottom: 2px solid var(--border);\n    }\n\n    .table th {\n      font-weight: 600;\n      color: var(--text-primary);\n      padding: 1rem 0.75rem;\n    }\n\n    .table td {\n      padding: 0.875rem 0.75rem;\n      border-bottom: 1px solid var(--border);\n      color: var(--text-primary);\n    }\n\n    .table-striped tbody tr:hover {\n      background-color: rgba(14, 165, 233, 0.03);\n    }\n\n    /* Responsive */\n    @media (max-width: 768px) {\n      main.container {\n        padding: 1rem;\n      }\n\n      .navbar-brand {\n        font-size: 1.25rem;\n      }\n\n      .nav-link {\n        padding: 0.75rem 0.5rem !important;\n      }\n    }\n  </style>\n\n  '
    yield from context.blocks['head'][0](context)
    yield '\n</head>\n<body>\n<!-- Modernized navbar with gradient and new styling -->\n<nav class="navbar navbar-expand-lg navbar-dark">\n  <div class="container-fluid">\n    <a class="navbar-brand" href="'
    yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.index'))
    yield '">\n      <img src="'
    yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'static', filename='logo.png'))
    yield '" alt="Logo" class="navbar-logo">\n      SLIS\n    </a>\n    <button class="navbar-toggler" type="button" data-bs-toggle="collapse"\n            data-bs-target="#navbarNav" aria-controls="navbarNav"\n            aria-expanded="false" aria-label="Toggle navigation">\n      <span class="navbar-toggler-icon"></span>\n    </button>\n    <div class="collapse navbar-collapse" id="navbarNav">\n      <ul class="navbar-nav ms-auto">\n        <li class="nav-item">\n          <a class="nav-link" href="'
    yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.index'))
    yield '">Home</a>\n        </li>\n        <li class="nav-item">\n          <a class="nav-link" href="'
    yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_manage'))
    yield '">Sanctions</a>\n        </li>\n        <li class="nav-item">\n          <a class="nav-link" href="'
    yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.screening_jobs'))
    yield '">Jobs</a>\n        </li>\n      </ul>\n    </div>\n  </div>\n</nav>\n\n<main class="container">\n  <!-- Enhanced alert system with new color scheme -->\n  '
    l_1_messages = context.call((undefined(name='get_flashed_messages') if l_0_get_flashed_messages is missing else l_0_get_flashed_messages), with_categories=True)
    pass
    yield '\n    '
    if l_1_messages:
        pass
        yield '\n      <div class="mb-4">\n        '
        for (l_2_category, l_2_message) in l_1_messages:
            _loop_vars = {}
            pass
            yield '\n          <div class="alert alert-'
            yield escape(l_2_category)
            yield ' alert-dismissible fade show" role="alert">\n            '
            yield escape(l_2_message)
            yield '\n            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>\n          </div>\n        '
        l_2_category = l_2_message = missing
        yield '\n      </div>\n    '
    yield '\n  '
    l_1_messages = missing
    yield '\n\n  '
    yield from context.blocks['content'][0](context)
    yield '\n</main>\n\n<script\n  src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"\n></script>\n\n'
    yield from context.blocks['scripts'][0](context)
    yield '\n</body>\n</html>'

def block_head(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    _block_vars = {}
    pass

def block_content(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    _block_vars = {}
    pass

def block_scripts(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    _block_vars = {}
    pass

blocks = {'head': block_head, 'content': block_content, 'scripts': block_scripts}
debug_info = '321=14&327=16&328=18&339=20&342=22&345=24&355=29&357=32&358=36&359=38&367=45&374=47&321=50&367=59&374=68'