from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'index.html'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    parent_template = None
    pass
    parent_template = environment.get_template('base.html', 'index.html')
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
    yield "\n<style>\n  /* Landing page (The Lobby) - Clean, action-focused design */\n  .lobby-container {\n    min-height: calc(100vh - 80px);\n    display: flex;\n    flex-direction: column;\n    justify-content: center;\n    align-items: center;\n    background: linear-gradient(135deg, rgba(14, 165, 233, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%);\n    padding: 2rem;\n  }\n\n  .lobby-header {\n    text-align: center;\n    margin-bottom: 3rem;\n    max-width: 600px;\n  }\n\n  .lobby-header h1 {\n    font-size: 2.5rem;\n    font-weight: 800;\n    color: var(--text-primary);\n    margin-bottom: 0.75rem;\n    letter-spacing: -0.5px;\n  }\n\n  .lobby-header p {\n    font-size: 1.1rem;\n    color: var(--text-secondary);\n    line-height: 1.6;\n    margin-bottom: 1.5rem;\n  }\n\n  .lobby-tagline {\n    display: inline-block;\n    background-color: rgba(14, 165, 233, 0.1);\n    border: 1px solid rgba(14, 165, 233, 0.2);\n    border-radius: 20px;\n    padding: 0.5rem 1.25rem;\n    font-size: 0.85rem;\n    font-weight: 500;\n    color: var(--primary-accent);\n    margin-bottom: 1.5rem;\n  }\n\n  /* Hero Actions Grid */\n  .lobby-actions {\n    display: grid;\n    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));\n    gap: 2rem;\n    margin-bottom: 3rem;\n    max-width: 900px;\n  }\n\n  .hero-card {\n    background: var(--surface);\n    border: 2px solid var(--border);\n    border-radius: 16px;\n    padding: 2.5rem;\n    text-align: center;\n    cursor: pointer;\n    transition: all 0.3s ease;\n    position: relative;\n    overflow: hidden;\n  }\n\n  .hero-card::before {\n    content: '';\n    position: absolute;\n    top: 0;\n    left: 0;\n    right: 0;\n    height: 4px;\n    background: linear-gradient(90deg, var(--primary-accent), var(--secondary));\n    transform: scaleX(0);\n    transform-origin: left;\n    transition: transform 0.3s ease;\n  }\n\n  .hero-card:hover {\n    border-color: var(--primary-accent);\n    box-shadow: 0 12px 32px rgba(14, 165, 233, 0.15);\n    transform: translateY(-4px);\n  }\n\n  .hero-card:hover::before {\n    transform: scaleX(1);\n  }\n\n  .hero-icon {\n    font-size: 3.5rem;\n    margin-bottom: 1.5rem;\n    display: block;\n  }\n\n  .hero-card h2 {\n    font-size: 1.4rem;\n    font-weight: 700;\n    color: var(--text-primary);\n    margin-bottom: 0.75rem;\n  }\n\n  .hero-card p {\n    color: var(--text-secondary);\n    font-size: 0.95rem;\n    line-height: 1.6;\n    margin-bottom: 1.75rem;\n  }\n\n  .hero-card .btn {\n    width: 100%;\n    padding: 0.8rem 1.5rem;\n    font-weight: 600;\n  }\n\n  .hero-card.bulk-screening .btn {\n    background-color: var(--primary-accent);\n    color: white;\n  }\n\n  .hero-card.bulk-screening .btn:hover {\n    background-color: #0284c7;\n  }\n\n  .hero-card.quick-search .btn {\n    background-color: var(--secondary);\n    color: white;\n  }\n\n  .hero-card.quick-search .btn:hover {\n    background-color: #4f46e5;\n  }\n\n  /* Version Badge - Bottom Right */\n  .version-widget {\n    position: fixed;\n    bottom: 2rem;\n    right: 2rem;\n    background: var(--surface);\n    border: 1px solid var(--border);\n    border-radius: 12px;\n    padding: 1rem 1.25rem;\n    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);\n    max-width: 250px;\n  }\n\n  .version-widget-title {\n    font-size: 0.75rem;\n    color: var(--text-light);\n    font-weight: 600;\n    text-transform: uppercase;\n    letter-spacing: 0.5px;\n    margin-bottom: 0.5rem;\n  }\n\n  .version-widget-content {\n    display: flex;\n    justify-content: space-between;\n    align-items: center;\n    gap: 1rem;\n  }\n\n  .version-info {\n    flex: 1;\n  }\n\n  .version-label {\n    font-size: 0.8rem;\n    color: var(--text-light);\n    margin-bottom: 0.25rem;\n  }\n\n  .version-value {\n    font-size: 0.95rem;\n    font-weight: 700;\n    color: var(--text-primary);\n  }\n\n  .version-badge {\n    display: inline-block;\n    background-color: var(--success);\n    color: white;\n    padding: 0.4rem 0.8rem;\n    border-radius: 6px;\n    font-size: 0.75rem;\n    font-weight: 600;\n  }\n\n  .btn-update-list {\n    padding: 0.5rem 1rem;\n    font-size: 0.8rem;\n    background-color: transparent;\n    border: 1px solid var(--border);\n    color: var(--text-primary);\n    border-radius: 6px;\n    cursor: pointer;\n    transition: all 0.2s ease;\n    white-space: nowrap;\n  }\n\n  .btn-update-list:hover {\n    background-color: var(--background);\n    border-color: var(--text-light);\n  }\n\n  /* Quick Stats */\n  .lobby-stats {\n    display: grid;\n    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));\n    gap: 1.5rem;\n    margin-top: 3rem;\n    max-width: 900px;\n    padding: 2rem;\n    background: rgba(14, 165, 233, 0.04);\n    border: 1px solid rgba(14, 165, 233, 0.1);\n    border-radius: 12px;\n  }\n\n  .stat-item {\n    text-align: center;\n  }\n\n  .stat-value {\n    font-size: 1.75rem;\n    font-weight: 800;\n    color: var(--primary-accent);\n    margin-bottom: 0.25rem;\n  }\n\n  .stat-label {\n    font-size: 0.85rem;\n    color: var(--text-secondary);\n    font-weight: 500;\n  }\n\n  /* Responsive */\n  @media (max-width: 768px) {\n    .lobby-container {\n      padding: 1.5rem;\n    }\n\n    .lobby-header h1 {\n      font-size: 2rem;\n    }\n\n    .lobby-header p {\n      font-size: 0.95rem;\n    }\n\n    .lobby-actions {\n      grid-template-columns: 1fr;\n      gap: 1.5rem;\n    }\n\n    .hero-card {\n      padding: 2rem;\n    }\n\n    .hero-icon {\n      font-size: 3rem;\n      margin-bottom: 1rem;\n    }\n\n    .hero-card h2 {\n      font-size: 1.2rem;\n    }\n\n    .version-widget {\n      position: relative;\n      bottom: auto;\n      right: auto;\n      margin-top: 2rem;\n      margin-left: auto;\n      margin-right: auto;\n    }\n\n    .lobby-stats {\n      grid-template-columns: repeat(2, 1fr);\n      gap: 1rem;\n    }\n  }\n\n  @media (max-width: 480px) {\n    .lobby-header h1 {\n      font-size: 1.5rem;\n    }\n\n    .hero-card {\n      padding: 1.5rem;\n    }\n\n    .hero-card h2 {\n      font-size: 1rem;\n    }\n\n    .hero-card p {\n      font-size: 0.85rem;\n    }\n\n    .lobby-stats {\n      grid-template-columns: 1fr;\n    }\n  }\n</style>\n"

def block_content(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    _block_vars = {}
    l_0_url_for = resolve('url_for')
    l_0_sanction_count = resolve('sanction_count')
    l_0_batch_count = resolve('batch_count')
    l_0_job_count = resolve('job_count')
    l_0_total_matches = resolve('total_matches')
    pass
    yield '\n<div class="lobby-container">\n  <!-- Header -->\n  <div class="lobby-header">\n    <div class="lobby-tagline">Sistem Keamanan Pembayaran</div>\n    <h1>Sanction List Intelligence Screening</h1>\n    <p>Lakukan screening nama, DOB, dan citizenship nasabah terhadap sanction list dengan akurat dan cepat.</p>\n  </div>\n\n  <!-- Main Actions -->\n  <div class="lobby-actions">\n    <!-- Quick Search -->\n    <div class="hero-card quick-search">\n      <span class="hero-icon">🔍</span>\n      <h2>Quick Search</h2>\n      <p>Screening instan untuk satu nasabah. Ketik nama dan dapatkan hasil langsung.</p>\n      <a href="'
    yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.search_by_name', _block_vars=_block_vars))
    yield '" class="btn">Mulai Pencarian</a>\n    </div>\n\n    <!-- Bulk Screening -->\n    <div class="hero-card bulk-screening">\n      <span class="hero-icon">📊</span>\n      <h2>Bulk Screening</h2>\n      <p>Upload file batch transaksi dan jalankan screening otomatis untuk ribuan records.</p>\n      <a href="'
    yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_upload', _block_vars=_block_vars))
    yield '" class="btn">Mulai Screening</a>\n    </div>\n  </div>\n\n  <!-- Quick Stats -->\n  <div class="lobby-stats">\n    <div class="stat-item">\n      <div class="stat-value">'
    yield escape(((undefined(name='sanction_count') if l_0_sanction_count is missing else l_0_sanction_count) or 0))
    yield '</div>\n      <div class="stat-label">Entitas Sanksi</div>\n    </div>\n    <div class="stat-item">\n      <div class="stat-value">'
    yield escape(((undefined(name='batch_count') if l_0_batch_count is missing else l_0_batch_count) or 0))
    yield '</div>\n      <div class="stat-label">Batch Terproses</div>\n    </div>\n    <div class="stat-item">\n      <div class="stat-value">'
    yield escape(((undefined(name='job_count') if l_0_job_count is missing else l_0_job_count) or 0))
    yield '</div>\n      <div class="stat-label">Screening Jobs</div>\n    </div>\n    <div class="stat-item">\n      <div class="stat-value">'
    yield escape(((undefined(name='total_matches') if l_0_total_matches is missing else l_0_total_matches) or 0))
    yield '</div>\n      <div class="stat-label">Matches Ditemukan</div>\n    </div>\n  </div>\n</div>\n\n<!-- Version Widget (Bottom Right) -->\n<div class="version-widget">\n  <div class="version-widget-title">Sanction List Status</div>\n  <div class="version-widget-content">\n    <div class="version-info">\n      <div class="version-label">Version</div>\n      <div class="version-value">Dec 2025</div>\n      <div style="margin-top: 0.5rem;">\n        <span class="version-badge">Updated 2h ago</span>\n      </div>\n    </div>\n    <button class="btn-update-list" onclick="alert(\'Update functionality coming soon\')">Update List</button>\n  </div>\n</div>\n'

blocks = {'head': block_head, 'content': block_content}
debug_info = '1=12&3=17&310=27&326=41&334=43&341=45&345=47&349=49&353=51'