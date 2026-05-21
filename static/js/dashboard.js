// ============================================
// SafeAlert Dashboard - Main JavaScript
// ============================================
let alarmBeepTimer = null;
let alarmAudioCtx = null;
const notifiedUserNotes = new Set();

function startEmergencyBeep() {
    if (alarmBeepTimer) return;
    const modal = document.getElementById('activeAlertModal');
    if (!modal) return;
    if (!window.AudioContext && !window.webkitAudioContext) return;

    const AudioCtor = window.AudioContext || window.webkitAudioContext;
    alarmAudioCtx = alarmAudioCtx || new AudioCtor();

    const beep = () => {
        if (!alarmAudioCtx) return;
        const osc = alarmAudioCtx.createOscillator();
        const gain = alarmAudioCtx.createGain();
        osc.type = 'square';
        osc.frequency.value = 880;
        gain.gain.value = 0.015;
        osc.connect(gain);
        gain.connect(alarmAudioCtx.destination);
        osc.start();
        setTimeout(() => {
            osc.stop();
            osc.disconnect();
            gain.disconnect();
        }, 140);
    };

    // pattern: beep-beep pause
    alarmBeepTimer = setInterval(() => {
        beep();
        setTimeout(beep, 220);
    }, 1800);
}

function stopEmergencyBeep() {
    if (alarmBeepTimer) {
        clearInterval(alarmBeepTimer);
        alarmBeepTimer = null;
    }
}

// Helper: Get CSRF token from cookies
function getCsrfToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    // Fallback: get from hidden input
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
}

// Helper: Show toast notification
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const icons = {
        success: 'bi-check-circle-fill',
        danger: 'bi-exclamation-triangle-fill',
        warning: 'bi-exclamation-circle-fill',
        info: 'bi-info-circle-fill'
    };
    
    const colors = {
        success: '#22c55e',
        danger: '#ef4444',
        warning: '#eab308',
        info: '#3b82f6'
    };
    
    const toastId = 'toast-' + Date.now();
    const html = `
        <div id="${toastId}" class="toast show" role="alert" style="background:#ffffff;border:1px solid ${colors[type]}33;border-radius:12px;min-width:320px;box-shadow:0 8px 24px rgba(90,70,40,.14);">
            <div class="toast-body d-flex align-items-center gap-2" style="color:#2c2416;">
                <i class="bi ${icons[type]}" style="color:${colors[type]};font-size:1.2rem;"></i>
                <span>${message}</span>
                <button type="button" class="btn-close ms-auto" onclick="this.closest('.toast').remove()" style="font-size:0.7rem;"></button>
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', html);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.style.transition = 'opacity 0.3s, transform 0.3s';
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            setTimeout(() => toast.remove(), 300);
        }
    }, 4000);
}

// Helper: Update timestamp
function updateTimestamp() {
    const el = document.getElementById('last-updated');
    if (el) {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        el.textContent = `${hours}:${minutes}:${seconds}`;
    }
}

function escapeHtml(value) {
    return String(value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function escapeAttr(value) {
    return escapeHtml(value).replaceAll('`', '&#096;');
}

// ============================================
// Tab Navigation
// ============================================
function switchTab(element, tabId) {
    // Hide all tab panels
    document.querySelectorAll('.tab-content-panel').forEach(panel => {
        panel.classList.add('d-none');
    });
    
    // Deactivate all nav links
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected tab
    const targetPanel = document.getElementById(tabId);
    if (targetPanel) {
        targetPanel.classList.remove('d-none');
        targetPanel.classList.add('tab-enter');
        requestAnimationFrame(() => {
            targetPanel.classList.remove('tab-enter');
        });
    }
    
    // Activate selected link
    element.classList.add('active');
}

function filterTableByBuilding(tableId, buildingId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    table.querySelectorAll('tbody tr[data-building-id]').forEach(row => {
        const matches = !buildingId || row.dataset.buildingId === buildingId;
        row.classList.toggle('d-none', !matches);
    });
}

// ============================================
// Building CRUD
// ============================================
function openBuildingModal(buildingId = null) {
    const modalEl = document.getElementById('buildingModal');
    const form = document.getElementById('building-form');
    if (!modalEl || !form) return;

    form.reset();
    document.getElementById('building-id').value = '';
    document.getElementById('building-remove-floor-plan').value = 'false';
    document.getElementById('building-plan-current').classList.add('d-none');
    document.getElementById('building-modal-title').textContent = 'Tambah Gedung';

    if (buildingId) {
        const row = document.getElementById(`building-row-${buildingId}`);
        if (!row) return;

        document.getElementById('building-id').value = buildingId;
        document.getElementById('building-name').value = row.dataset.name || '';
        document.getElementById('building-modal-title').textContent = 'Edit Gedung';
        if (row.dataset.floorPlanUrl) {
            document.getElementById('building-plan-current').classList.remove('d-none');
            const planLink = document.getElementById('building-plan-link');
            planLink.href = row.dataset.floorPlanUrl;
        }
    }

    bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

function serializeBuildingForm() {
    const formData = new FormData();
    const floorPlan = document.getElementById('building-floor-plan').files[0];
    formData.append('name', document.getElementById('building-name').value.trim());
    formData.append('remove_floor_plan', document.getElementById('building-remove-floor-plan').value);
    if (floorPlan) {
        formData.append('floor_plan', floorPlan);
    }
    return formData;
}

function markFloorPlanForRemoval() {
    document.getElementById('building-remove-floor-plan').value = 'true';
    document.getElementById('building-plan-current').classList.add('d-none');
    document.getElementById('building-floor-plan').value = '';
}

function buildingRowHtml(building) {
    const floorPlanUrl = building.floor_plan_url || '';
    const floorPlanHtml = floorPlanUrl
        ? `<a href="${escapeAttr(floorPlanUrl)}" target="_blank" rel="noopener"><img src="${escapeAttr(floorPlanUrl)}" alt="Denah ${escapeAttr(building.name)}" class="building-plan-thumb"></a>`
        : '<span class="text-muted">Belum ada denah</span>';

    return `
        <tr id="building-row-${building.id}"
            data-building-id="${building.id}"
            data-name="${escapeAttr(building.name)}"
            data-floor-plan-url="${escapeAttr(floorPlanUrl)}">
            <td class="fw-semibold building-name-cell">${escapeHtml(building.name)}</td>
            <td class="building-plan-cell">${floorPlanHtml}</td>
            <td>
                <div class="action-group">
                    <button class="btn btn-sm btn-outline-primary" type="button" onclick="openBuildingModal(${building.id})" title="Edit">
                        <i class="bi bi-pencil-square"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" type="button" onclick="deleteBuilding(${building.id})" title="Hapus">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

function upsertBuildingRow(building) {
    const emptyRow = document.getElementById('building-empty-row');
    if (emptyRow) emptyRow.remove();

    const tableBody = document.querySelector('#table-buildings tbody');
    if (!tableBody) return;

    const existing = document.getElementById(`building-row-${building.id}`);
    const html = buildingRowHtml(building);
    if (existing) {
        existing.outerHTML = html;
    } else {
        tableBody.insertAdjacentHTML('afterbegin', html);
    }
}

const buildingForm = document.getElementById('building-form');
if (buildingForm) {
    buildingForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const buildingId = document.getElementById('building-id').value;
        const payload = serializeBuildingForm();
        if (!payload.get('name')) {
            showToast('Nama gedung wajib diisi.', 'warning');
            return;
        }

        const submitBtn = document.getElementById('building-submit-btn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Menyimpan...';

        fetch(buildingId ? `/dashboard/api/buildings/${buildingId}/` : '/dashboard/api/buildings/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            body: payload
        })
        .then(response => response.json().then(data => {
            if (!response.ok) throw new Error(data.message || 'Gagal menyimpan gedung');
            return data;
        }))
        .then(data => {
            upsertBuildingRow(data.building);
            bootstrap.Modal.getOrCreateInstance(document.getElementById('buildingModal')).hide();
            showToast(data.message || 'Gedung berhasil disimpan', 'success');
        })
        .catch(error => {
            showToast(error.message, 'danger');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-save me-1"></i>Simpan Gedung';
        });
    });
}

function deleteBuilding(buildingId) {
    const row = document.getElementById(`building-row-${buildingId}`);
    const buildingName = row?.dataset.name || 'gedung ini';
    if (!confirm(`Hapus ${buildingName}?`)) return;

    fetch(`/dashboard/api/buildings/${buildingId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json().then(data => {
        if (!response.ok) throw new Error(data.message || 'Gagal menghapus gedung');
        return data;
    }))
    .then(data => {
        row?.remove();
        showToast(data.message || 'Gedung berhasil dihapus', 'success');
    })
    .catch(error => {
        showToast(error.message, 'danger');
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.stat-card');
    cards.forEach((card, idx) => {
        card.style.animationDelay = `${idx * 70}ms`;
    });

    startEmergencyBeep();
});

window.addEventListener('beforeunload', stopEmergencyBeep);

// ============================================
// Verify User (Approve / Reject)
// ============================================
function verifyUser(profileId, newStatus) {
    const action = newStatus === 'active' ? 'memverifikasi' : 'menolak';
    if (!confirm(`Apakah Anda yakin ingin ${action} user ini?`)) return;
    
    fetch(`/api/users/${profileId}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => {
        if (!response.ok) throw new Error('Gagal memperbarui status');
        return response.json();
    })
    .then(data => {
        // Remove row from pending table
        const row = document.getElementById(`pending-row-${profileId}`);
        if (row) {
            row.style.transition = 'opacity 0.3s, transform 0.3s';
            row.style.opacity = '0';
            row.style.transform = 'translateX(-20px)';
            setTimeout(() => row.remove(), 300);
        }
        
        const statusText = newStatus === 'active' ? 'diverifikasi' : 'ditolak';
        showToast(`User berhasil ${statusText}`, newStatus === 'active' ? 'success' : 'warning');
        refreshStats();
    })
    .catch(error => {
        showToast('Gagal memperbarui status user: ' + error.message, 'danger');
    });
}

// ============================================
// Update User Status (Dropdown)
// ============================================
function updateUserStatus(profileId, newStatus) {
    fetch(`/api/users/${profileId}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => {
        if (!response.ok) throw new Error('Gagal memperbarui status');
        return response.json();
    })
    .then(data => {
        showToast('Status user berhasil diperbarui', 'success');
        refreshStats();
    })
    .catch(error => {
        showToast('Gagal memperbarui status: ' + error.message, 'danger');
    });
}

function updateDisasterStatus(selectEl) {
    const confirmationId = selectEl.dataset.confirmationId;
    const newStatus = selectEl.value;
    if (!confirmationId || !newStatus) return;

    fetch(`/api/confirmations/${confirmationId}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => {
        if (!response.ok) throw new Error('Gagal memperbarui status bencana');
        return response.json();
    })
    .then(data => {
        applyDisasterStatusSelect(selectEl, data.status);
        showToast('Status bencana user berhasil diperbarui', 'success');
    })
    .catch(error => {
        showToast('Gagal memperbarui status bencana: ' + error.message, 'danger');
    });
}

function applyDisasterStatusSelect(selectEl, statusValue) {
    if (!selectEl) return;
    selectEl.value = statusValue;
    selectEl.classList.remove('status-safe', 'status-needs_help', 'status-trapped', 'status-no_response', 'status-empty');
    selectEl.classList.add(`status-${statusValue || 'empty'}`);
}

// ============================================
// Send Alarm
// ============================================
const alarmForm = document.getElementById('alarm-form');
if (alarmForm) {
    alarmForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const buildingId = document.getElementById('alarm-building').value;
        const alertType = document.getElementById('alarm-type').value;
        const title = document.getElementById('alarm-title').value.trim();
        const message = document.getElementById('alarm-message').value.trim();
        
        if (!title || !message) {
            showToast('Judul dan pesan alarm harus diisi!', 'warning');
            return;
        }
        
        const buildingName = document.getElementById('alarm-building').selectedOptions[0]?.textContent || 'gedung terpilih';
        if (!confirm(`PERHATIAN!\n\nAnda akan mengirim alarm darurat hanya ke user aktif di ${buildingName}.\n\nLanjutkan?`)) return;
        
        const btn = document.getElementById('btn-send-alarm');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Mengirim alarm...';
        
        fetch('/api/alerts/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                building: parseInt(buildingId),
                alert_type: alertType,
                title: title,
                description: message,
                severity: 3
            })
        })
        .then(response => {
            if (!response.ok) throw new Error('Gagal mengirim alarm');
            return response.json();
        })
        .then(data => {
            showToast('Alarm darurat berhasil dikirim!', 'danger');
            // Reload page to show active alert state
            setTimeout(() => location.reload(), 1000);
        })
        .catch(error => {
            showToast('Gagal mengirim alarm: ' + error.message, 'danger');
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-broadcast me-2"></i>KIRIM ALARM KE GEDUNG TERPILIH';
        });
    });
}

// ============================================
// Resolve / Cancel Alert
// ============================================
function resolveAlert(alertId) {
    if (!confirm('Tandai alarm ini sebagai SELESAI?')) return;
    stopEmergencyBeep();
    
    fetch(`/api/alerts/${alertId}/resolve/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Gagal menyelesaikan alarm');
        showToast('Alarm berhasil diselesaikan', 'success');
        setTimeout(() => location.reload(), 1000);
    })
    .catch(error => {
        showToast('Gagal: ' + error.message, 'danger');
    });
}

function cancelAlert(alertId) {
    if (!confirm('BATALKAN alarm ini?\nNotifikasi pembatalan akan dikirim ke semua user.')) return;
    stopEmergencyBeep();
    
    fetch(`/api/alerts/${alertId}/cancel/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Gagal membatalkan alarm');
        showToast('Alarm berhasil dibatalkan', 'warning');
        setTimeout(() => location.reload(), 1000);
    })
    .catch(error => {
        showToast('Gagal: ' + error.message, 'danger');
    });
}

// ============================================
// Load Confirmations for Active Alert
// ============================================
function loadConfirmations(alertId) {
    fetch(`/api/confirmations/alert_confirmations/?alert_id=${alertId}`, {
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        updateConfirmationUI(data);
    })
    .catch(error => {
        console.error('Error loading confirmations:', error);
    });
}

function updateConfirmationUI(confirmations) {
    // Count statuses
    let safe = 0, trapped = 0, needsHelp = 0, noResponse = 0;
    confirmations.forEach(c => {
        switch(c.status) {
            case 'safe': safe++; break;
            case 'trapped': trapped++; break;
            case 'needs_help': needsHelp++; break;
            case 'no_response': noResponse++; break;
        }
    });
    
    // Update counters
    const elSafe = document.getElementById('conf-safe');
    const elTrapped = document.getElementById('conf-trapped');
    const elNeedsHelp = document.getElementById('conf-needs-help');
    const elNoResponse = document.getElementById('conf-no-response');
    
    if (elSafe) elSafe.textContent = safe;
    if (elTrapped) elTrapped.textContent = trapped;
    if (elNeedsHelp) elNeedsHelp.textContent = needsHelp;
    if (elNoResponse) elNoResponse.textContent = noResponse;
    
    // Build confirmation list
    const listEl = document.getElementById('confirmation-list');
    if (!listEl) return;
    
    let html = '';
    confirmations.forEach(c => {
        const userName = c.user ? (c.user.first_name + ' ' + c.user.last_name).trim() || c.user.username : 'Unknown';
        const statusLabels = {
            'safe': 'Aman',
            'trapped': 'Terjebak',
            'needs_help': 'Butuh Bantuan',
            'no_response': 'Belum Merespon'
        };
        const statusLabel = statusLabels[c.status] || c.status;
        const location = escapeHtml(c.location || 'Lokasi tidak diketahui');
        updateUserNotesCell(c, userName);
        
        html += `
            <div class="confirmation-card status-${c.status}">
                <div class="confirmation-main">
                    <div class="fw-semibold confirmation-user-name">${escapeHtml(userName)}</div>
                    <div class="confirmation-meta">
                        <i class="bi bi-geo-alt me-1"></i>
                        <span>${location}</span>
                    </div>
                </div>
                <span class="badge badge-status badge-${c.status}">${statusLabel}</span>
            </div>
        `;
    });
    
    listEl.innerHTML = html || '<p class="text-muted text-center">Belum ada konfirmasi</p>';
    
    updateTimestamp();
}

function updateUserNotesCell(confirmation, userName) {
    if (!confirmation.user || !confirmation.user.id) return;

    const userId = confirmation.user.id;
    updateDisasterStatusCell(userId, confirmation);

    const notesCell = document.getElementById(`user-notes-${userId}`);
    if (!notesCell) return;

    const rawNotes = (confirmation.notes || '').trim();
    const rawLocation = (confirmation.location || '').trim();
    if (!rawNotes && !rawLocation) return;

    const notes = escapeHtml(rawNotes);
    const location = escapeHtml(rawLocation || 'Lokasi tidak diketahui');

    notesCell.innerHTML = `
        <div class="user-notes-alert">
            <div class="user-notes-meta"><i class="bi bi-geo-alt me-1"></i>${location}</div>
        </div>
    `;

    const notificationKey = `${confirmation.id}:${rawNotes}`;
    if (rawNotes && !notifiedUserNotes.has(notificationKey)) {
        notifiedUserNotes.add(notificationKey);
        showToast(`Notes baru dari ${escapeHtml(userName)}: ${notes}`, 'warning');
    }
}

function updateDisasterStatusCell(userId, confirmation) {
    const row = document.querySelector(`#table-users tbody tr[data-user-id="${userId}"]`);
    if (!row) return;

    const selectEl = row.querySelector('.disaster-status-select');
    if (!selectEl) return;

    selectEl.dataset.confirmationId = confirmation.id || selectEl.dataset.confirmationId || '';
    selectEl.disabled = !selectEl.dataset.confirmationId;
    applyDisasterStatusSelect(selectEl, confirmation.status);
}

// ============================================
// Refresh Stats (Polling)
// ============================================
function refreshStats() {
    fetch('/dashboard/api/stats/', {
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        // Update stat cards
        const totalEl = document.getElementById('stat-total-users');
        const activeEl = document.getElementById('stat-active-users');
        const pendingEl = document.getElementById('stat-pending-users');
        const alertsEl = document.getElementById('stat-active-alerts');
        
        if (totalEl) totalEl.textContent = data.total_users;
        if (activeEl) activeEl.textContent = data.active_users;
        if (pendingEl) pendingEl.textContent = data.pending_users;
        if (alertsEl) alertsEl.textContent = data.active_alerts;
        
        // Update pending badge in sidebar
        const pendingBadge = document.getElementById('pending-count-badge');
        if (pendingBadge) pendingBadge.textContent = data.pending_users;
        
        updateTimestamp();
    })
    .catch(error => {
        console.error('Error refreshing stats:', error);
    });
}
