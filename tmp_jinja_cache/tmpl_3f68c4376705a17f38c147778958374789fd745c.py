from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'screening_jobs.html'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    parent_template = None
    pass
    parent_template = environment.get_template('base.html', 'screening_jobs.html')
    for name, parent_block in parent_template.blocks.items():
        context.blocks.setdefault(name, []).append(parent_block)
    yield from parent_template.root_render_func(context)

def block_content(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    _block_vars = {}
    l_0_jobs = resolve('jobs')
    l_0_url_for = resolve('url_for')
    try:
        t_1 = environment.filters['format']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'format' found.")
    pass
    yield '\n<div class="row">\n  <div class="col">\n    <div class="d-flex justify-content-between align-items-center mb-4">\n      <h2>Screening Jobs</h2>\n      <button\n        class="btn btn-outline-primary btn-sm"\n        onclick="location.reload()"\n      >\n        ↻ Refresh Data\n      </button>\n    </div>\n\n    '
    if (undefined(name='jobs') if l_0_jobs is missing else l_0_jobs):
        pass
        yield '\n    <div class="table-responsive">\n      <table class="table table-striped table-hover align-middle">\n        <thead>\n          <tr>\n            <th>ID</th>\n            <th>Batch</th>\n            <th>Status</th>\n            <th style="width: 20%">Progress</th>\n            <th>Transaksi</th>\n            <th>Matches</th>\n            <th>Started</th>\n            <th>Finished</th>\n            <th>Actions</th>\n          </tr>\n        </thead>\n        <tbody>\n          '
        for l_1_j in (undefined(name='jobs') if l_0_jobs is missing else l_0_jobs):
            l_1_is_success = l_1_is_failure = l_1_is_canceled = l_1_is_finished = l_1_bar_width = l_1_bar_class = missing
            _loop_vars = {}
            pass
            yield '\n          '
            l_1_is_success = (environment.getattr(l_1_j, 'status') in ['SUCCESS', 'DONE'])
            _loop_vars['is_success'] = l_1_is_success
            yield '\n          '
            l_1_is_failure = (environment.getattr(l_1_j, 'status') in ['FAILURE', 'FAILED'])
            _loop_vars['is_failure'] = l_1_is_failure
            yield '\n          '
            l_1_is_canceled = (environment.getattr(l_1_j, 'status') == 'CANCELED')
            _loop_vars['is_canceled'] = l_1_is_canceled
            yield '\n          '
            l_1_is_finished = (((undefined(name='is_success') if l_1_is_success is missing else l_1_is_success) or (undefined(name='is_failure') if l_1_is_failure is missing else l_1_is_failure)) or (undefined(name='is_canceled') if l_1_is_canceled is missing else l_1_is_canceled))
            _loop_vars['is_finished'] = l_1_is_finished
            yield '\n          '
            l_1_bar_width = (100 if (undefined(name='is_success') if l_1_is_success is missing else l_1_is_success) else (environment.getattr(l_1_j, 'progress_percentage') or 0))
            _loop_vars['bar_width'] = l_1_bar_width
            yield '\n          '
            l_1_bar_class = ('bg-success' if (undefined(name='is_success') if l_1_is_success is missing else l_1_is_success) else ('bg-danger' if (undefined(name='is_failure') if l_1_is_failure is missing else l_1_is_failure) else ('bg-secondary' if (undefined(name='is_canceled') if l_1_is_canceled is missing else l_1_is_canceled) else ('progress-bar-animated bg-warning' if (environment.getattr(l_1_j, 'status') == 'RUNNING') else 'bg-secondary'))))
            _loop_vars['bar_class'] = l_1_bar_class
            yield '\n\n          <tr\n            data-job-id="'
            yield escape(environment.getattr(l_1_j, 'id'))
            yield '"\n            data-status="'
            yield escape(environment.getattr(l_1_j, 'status'))
            yield '"\n            class="job-row"\n          >\n            <td><strong>#'
            yield escape(environment.getattr(l_1_j, 'id'))
            yield '</strong></td>\n            <td>Batch #'
            yield escape(environment.getattr(l_1_j, 'batch_id'))
            yield '</td>\n            <td>\n              '
            if (undefined(name='is_success') if l_1_is_success is missing else l_1_is_success):
                pass
                yield '\n              <span class="badge bg-success">SUCCESS</span>\n              '
            elif (undefined(name='is_failure') if l_1_is_failure is missing else l_1_is_failure):
                pass
                yield '\n              <span class="badge bg-danger">FAILURE</span>\n              '
            elif (environment.getattr(l_1_j, 'status') == 'RUNNING'):
                pass
                yield '\n              <span class="badge bg-warning text-dark">RUNNING</span>\n              '
            elif (undefined(name='is_canceled') if l_1_is_canceled is missing else l_1_is_canceled):
                pass
                yield '\n              <span class="badge bg-secondary">CANCELED</span>\n              '
            else:
                pass
                yield '\n              <span class="badge bg-secondary">'
                yield escape(environment.getattr(l_1_j, 'status'))
                yield '</span>\n              '
            yield '\n            </td>\n            <td>\n              <div\n                class="progress"\n                style="height: 20px; background-color: #e2e8f0"\n              >\n                <div\n                  class="progress-bar progress-bar-striped '
            yield escape((undefined(name='bar_class') if l_1_bar_class is missing else l_1_bar_class))
            yield '"\n                  role="progressbar"\n                  style="--bar-width: '
            yield escape((undefined(name='bar_width') if l_1_bar_width is missing else l_1_bar_width))
            yield '%; width: var(--bar-width);"\n                  aria-valuenow="'
            yield escape((undefined(name='bar_width') if l_1_bar_width is missing else l_1_bar_width))
            yield '"\n                  aria-valuemin="0"\n                  aria-valuemax="100"\n                >\n                  <span class="progress-text small fw-bold">\n                    '
            yield escape(t_1('%.0f', (undefined(name='bar_width') if l_1_bar_width is missing else l_1_bar_width)))
            yield '%\n                  </span>\n                </div>\n              </div>\n            </td>\n            <td class="transactions-info">\n              <span class="processed fw-bold">\n                '
            yield escape((environment.getattr(l_1_j, 'total_transactions') if (undefined(name='is_success') if l_1_is_success is missing else l_1_is_success) else (environment.getattr(l_1_j, 'processed_transactions') or 0)))
            yield '\n              </span>\n              <span class="text-muted small">/</span>\n              <span class="total text-muted small"\n                >'
            yield escape((environment.getattr(l_1_j, 'total_transactions') or 0))
            yield '</span\n              >\n            </td>\n\n            <td class="matches-count fw-bold text-danger">\n              '
            yield escape((environment.getattr(l_1_j, 'total_matches') or 0))
            yield '\n            </td>\n            <td class="small text-muted">\n              '
            yield escape((context.call(environment.getattr(environment.getattr(l_1_j, 'started_at'), 'strftime'), '%Y-%m-%d %H:%M', _loop_vars=_loop_vars) if environment.getattr(l_1_j, 'started_at') else '-'))
            yield '\n            </td>\n            <td class="small text-muted">\n              '
            yield escape((context.call(environment.getattr(environment.getattr(l_1_j, 'finished_at'), 'strftime'), '%Y-%m-%d %H:%M', _loop_vars=_loop_vars) if environment.getattr(l_1_j, 'finished_at') else '-'))
            yield '\n            </td>\n            <td>\n              '
            if (undefined(name='is_success') if l_1_is_success is missing else l_1_is_success):
                pass
                yield '\n              <a\n                href="'
                yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.screening_job_detail', job_id=environment.getattr(l_1_j, 'id'), _loop_vars=_loop_vars))
                yield '"\n                class="btn btn-sm btn-primary"\n              >\n                Lihat Hasil\n              </a>\n              '
            elif (undefined(name='is_failure') if l_1_is_failure is missing else l_1_is_failure):
                pass
                yield '\n              <button class="btn btn-sm btn-outline-danger" disabled>\n                Error\n              </button>\n              '
            elif (environment.getattr(l_1_j, 'status') in ['RUNNING', 'PENDING']):
                pass
                yield '\n              <button\n                class="btn btn-sm btn-outline-danger"\n                onclick="cancelJob('
                yield escape(environment.getattr(l_1_j, 'id'))
                yield ')"\n              >\n                Batalkan\n              </button>\n              '
            elif (undefined(name='is_canceled') if l_1_is_canceled is missing else l_1_is_canceled):
                pass
                yield '\n              <button class="btn btn-sm btn-outline-secondary" disabled>\n                Dibatalkan\n              </button>\n              '
            else:
                pass
                yield '\n              <button class="btn btn-sm btn-outline-secondary" disabled>\n                Processing...\n              </button>\n              '
            yield '\n            </td>\n          </tr>\n          '
        l_1_j = l_1_is_success = l_1_is_failure = l_1_is_canceled = l_1_is_finished = l_1_bar_width = l_1_bar_class = missing
        yield '\n        </tbody>\n      </table>\n    </div>\n    '
    else:
        pass
        yield '\n    <div class="alert alert-info d-flex align-items-center">\n      <div class="me-2">ℹ️</div>\n      <div>\n        Belum ada screening job.\n        <a href="'
        yield escape(context.call((undefined(name='url_for') if l_0_url_for is missing else l_0_url_for), 'web.sanctions_upload', _block_vars=_block_vars))
        yield '" class="alert-link"\n          >Mulai screening baru</a\n        >.\n      </div>\n    </div>\n    '
    yield '\n  </div>\n</div>\n\n<script>\n  document.addEventListener("DOMContentLoaded", function () {\n    const runningRows = document.querySelectorAll(\'tr[data-status="RUNNING"]\');\n    const jobIds = Array.from(runningRows).map((row) => row.dataset.jobId);\n\n    window.cancelJob = async function (jobId) {\n      const ok = confirm(`Batalkan job #${jobId}?`);\n      if (!ok) return;\n\n      try {\n        const resp = await fetch(`/api/screening/jobs/${jobId}/cancel`, {\n          method: "POST",\n          headers: { "Content-Type": "application/json" },\n        });\n        if (!resp.ok) {\n          const data = await resp.json().catch(() => ({}));\n          alert(data.error || `Gagal membatalkan job (HTTP ${resp.status})`);\n          return;\n        }\n        setTimeout(() => location.reload(), 300);\n      } catch (e) {\n        alert(`Network error: ${e}`);\n      }\n    };\n\n    if (jobIds.length > 0) {\n      console.log("Monitoring jobs:", jobIds);\n\n      const pollInterval = setInterval(() => {\n        jobIds.forEach((jobId) => {\n          fetch(`/api/screening/jobs/${jobId}/progress`)\n            .then((response) => {\n              if (!response.ok) {\n                console.error("Fetch error:", response.status);\n                return null;\n              }\n              return response.json();\n            })\n            .then((data) => {\n              if (!data) return;\n\n              // --- DEBUGGING: Lihat isi data di Console Browser ---\n              console.log(`Job ${jobId} Data:`, data);\n              // ----------------------------------------------------\n\n              const row = document.querySelector(`tr[data-job-id="${jobId}"]`);\n              if (!row) return;\n\n              // 1. Logika Penentuan Persentase (Fallback agar aman)\n              // Backend mungkin mengirim \'percent\' (dari Redis) atau \'progress_percentage\' (dari DB)\n              let rawPercent = data.percent;\n              if (rawPercent === undefined || rawPercent === null) {\n                rawPercent = data.progress_percentage;\n              }\n              const pct = Math.round(rawPercent || 0);\n\n              // 2. Update Progress Bar Visual\n              const progressBar = row.querySelector(".progress-bar");\n              const progressText = row.querySelector(".progress-text");\n\n              if (progressBar) {\n                progressBar.style.width = `${pct}%`;\n                progressBar.setAttribute("aria-valuenow", pct);\n\n                // Hapus class \'bg-warning\' jika sudah selesai (opsional)\n                if (pct >= 100) {\n                  progressBar.classList.remove("bg-warning");\n                  progressBar.classList.add("bg-success");\n                }\n              }\n\n              if (progressText) {\n                progressText.textContent = `${pct}%`;\n              }\n\n              // 3. Update Angka Teks\n              const processedSpan = row.querySelector(".processed");\n              const totalSpan = row.querySelector(".total");\n              const matchesCell = row.querySelector(".matches-count");\n\n              // Gunakan fallback \'processed_transactions\' jika \'processed\' kosong\n              if (processedSpan)\n                processedSpan.textContent =\n                  data.processed ?? data.processed_transactions ?? 0;\n              if (totalSpan)\n                totalSpan.textContent =\n                  data.total ?? data.total_transactions ?? 0;\n              if (matchesCell)\n                matchesCell.textContent =\n                  data.matches ?? data.total_matches ?? 0;\n\n              // 4. Auto Reload jika Status Berubah (Selesai/Gagal)\n              // Kita cek jika status data berbeda dengan status di atribut HTML awal\n              if (data.status === "SUCCESS" || data.status === "FAILURE" || data.status === "CANCELED") {\n                console.log(\n                  `Job ${jobId} finished with status ${data.status}. Reloading...`\n                );\n                clearInterval(pollInterval);\n                setTimeout(() => location.reload(), 1000);\n              }\n            })\n            .catch((error) => {\n              console.error(`Network Error job ${jobId}:`, error);\n            });\n        });\n      }, 500);\n\n      window.addEventListener("beforeunload", () => {\n        clearInterval(pollInterval);\n      });\n    }\n  });\n</script>\n'

blocks = {'content': block_content}
debug_info = '1=12&14=34&31=37&32=42&33=45&34=48&35=51&36=54&37=57&40=60&41=62&44=64&45=66&47=68&49=71&51=74&53=77&56=83&65=86&67=88&68=90&73=92&80=94&85=96&90=98&93=100&97=102&101=104&103=107&108=109&112=112&115=115&119=117&139=129'