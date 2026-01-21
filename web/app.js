/**
 * Carte Blanche - Frontend Application
 * API 통신 및 UI 인터랙션 로직
 */

const API_BASE = 'http://localhost:5000/api';

// State
let rules = [];
let selectedRuleId = null;
let isEditing = false;

// DOM Elements
const ruleList = document.getElementById('ruleList');
const editorEmpty = document.getElementById('editorEmpty');
const editorForm = document.getElementById('editorForm');
const formTitle = document.getElementById('formTitle');
const watcherStatus = document.getElementById('watcherStatus');
const toggleWatcherBtn = document.getElementById('toggleWatcher');

// Form Elements
const ruleName = document.getElementById('ruleName');
const ruleEnabled = document.getElementById('ruleEnabled');
const triggerPath = document.getElementById('triggerPath');
const triggerExtensions = document.getElementById('triggerExtensions');
const actionType = document.getElementById('actionType');
const outputPath = document.getElementById('outputPath');
const workflowSelectContainer = document.getElementById('workflowSelectContainer');
const workflowSelect = document.getElementById('workflowSelect');

// ==================== API Functions ====================

async function fetchRules() {
  try {
    const response = await fetch(`${API_BASE}/rules`);
    const data = await response.json();
    if (data.success) {
      rules = data.rules;
      renderRuleList();
    }
  } catch (error) {
    showToast('규칙을 불러올 수 없습니다', 'error');
    console.error('Error fetching rules:', error);
  }
}

async function saveRule(ruleData) {
  try {
    const method = selectedRuleId ? 'PUT' : 'POST';
    const url = selectedRuleId
      ? `${API_BASE}/rules/${selectedRuleId}`
      : `${API_BASE}/rules`;

    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ruleData)
    });

    const data = await response.json();
    if (data.success) {
      showToast(selectedRuleId ? '규칙이 수정되었습니다' : '규칙이 추가되었습니다', 'success');
      await fetchRules();
      hideEditor();
    } else {
      showToast(data.error || '저장 실패', 'error');
    }
  } catch (error) {
    showToast('저장 중 오류가 발생했습니다', 'error');
    console.error('Error saving rule:', error);
  }
}

async function deleteRule(ruleId) {
  if (!confirm('이 규칙을 삭제하시겠습니까?')) return;

  try {
    const response = await fetch(`${API_BASE}/rules/${ruleId}`, {
      method: 'DELETE'
    });

    const data = await response.json();
    if (data.success) {
      showToast('규칙이 삭제되었습니다', 'success');
      if (selectedRuleId === ruleId) {
        hideEditor();
      }
      await fetchRules();
    }
  } catch (error) {
    showToast('삭제 중 오류가 발생했습니다', 'error');
    console.error('Error deleting rule:', error);
  }
}

async function fetchWatcherStatus() {
  try {
    const response = await fetch(`${API_BASE}/watcher/status`);
    const data = await response.json();
    updateWatcherUI(data.running);
  } catch (error) {
    console.error('Error fetching watcher status:', error);
  }
}

async function toggleWatcher() {
  const isRunning = watcherStatus.classList.contains('running');
  const endpoint = isRunning ? 'stop' : 'start';

  try {
    const response = await fetch(`${API_BASE}/watcher/${endpoint}`, {
      method: 'POST'
    });

    const data = await response.json();
    if (data.success) {
      updateWatcherUI(!isRunning);
      showToast(isRunning ? '감시가 중지되었습니다' : '감시가 시작되었습니다', 'success');
    }
  } catch (error) {
    showToast('Watcher 제어 중 오류가 발생했습니다', 'error');
    console.error('Error toggling watcher:', error);
  }
}

async function fetchWorkflows() {
  try {
    const response = await fetch(`${API_BASE}/workflows`);
    const data = await response.json();
    if (data.success) {
      workflowSelect.innerHTML = data.workflows.map(wf =>
        `<option value="${wf.filename}">${wf.name}</option>`
      ).join('');
    }
  } catch (error) {
    console.error('Error fetching workflows:', error);
  }
}

async function openPicker(targetId, mode = 'folder') {
  try {
    const response = await fetch(`${API_BASE}/utils/picker?mode=${mode}`);
    const data = await response.json();
    if (data.success) {
      const input = document.getElementById(targetId);
      if (input) {
        input.value = data.path;
        // Trigger manual update if needed
        input.dispatchEvent(new Event('input'));
      }
    } else if (data.error !== 'Cancelled') {
      showToast('경로 선택 중 오류 발생', 'error');
    }
  } catch (error) {
    console.error('Error opening picker:', error);
  }
}

// ==================== UI Functions ====================

function renderRuleList() {
  ruleList.innerHTML = rules.map(rule => `
    <li class="rule-item ${rule.id === selectedRuleId ? 'selected' : ''}" 
        data-id="${rule.id}">
      <div class="rule-item-header">
        <span class="rule-item-name">${rule.name}</span>
        <span class="rule-item-badge ${rule.enabled ? '' : 'disabled'}">
          ${rule.enabled ? '활성' : '비활성'}
        </span>
      </div>
      <div class="rule-item-info">
        <span>📁 ${rule.trigger?.path || '경로 없음'}</span>
        <span>📄 ${rule.trigger?.extensions?.join(', ') || '모든 파일'}</span>
      </div>
      <button class="rule-item-delete" onclick="event.stopPropagation(); deleteRule('${rule.id}')">✕</button>
    </li>
  `).join('');

  // Add click handlers
  document.querySelectorAll('.rule-item').forEach(item => {
    item.addEventListener('click', () => selectRule(item.dataset.id));
  });
}

function selectRule(ruleId) {
  selectedRuleId = ruleId;
  const rule = rules.find(r => r.id === ruleId);

  if (rule) {
    isEditing = true;
    formTitle.textContent = '규칙 편집';

    ruleName.value = rule.name || '';
    ruleEnabled.checked = rule.enabled !== false;
    triggerPath.value = rule.trigger?.path || '';
    triggerExtensions.value = rule.trigger?.extensions?.join(', ') || '';
    actionType.value = rule.action?.type || 'process_txt';
    outputPath.value = rule.action?.output_path || '';

    // 워크플로우 선택 연동
    if (actionType.value === 'run_workflow') {
      workflowSelectContainer.style.display = 'block';
      workflowSelect.value = rule.action?.args?.workflow_name || '';
    } else {
      workflowSelectContainer.style.display = 'none';
    }

    showEditor();
    showBatchSection();
    renderRuleList();
  }
}

function showEditor() {
  editorEmpty.style.display = 'none';
  editorForm.style.display = 'block';
  editorForm.classList.add('fade-in');
}

function hideEditor() {
  editorForm.style.display = 'none';
  editorEmpty.style.display = 'flex';
  selectedRuleId = null;
  isEditing = false;
  clearForm();
  renderRuleList();
}

function clearForm() {
  ruleName.value = '';
  ruleEnabled.checked = true;
  triggerPath.value = '';
  triggerExtensions.value = '';
  actionType.value = 'process_txt';
  outputPath.value = '';
  workflowSelectContainer.style.display = 'none';
}

function showNewRuleForm() {
  selectedRuleId = null;
  isEditing = false;
  formTitle.textContent = '새 규칙 만들기';
  clearForm();
  showEditor();
  renderRuleList();
}

function updateWatcherUI(isRunning) {
  const statusText = watcherStatus.querySelector('.status-text');
  const btnIcon = toggleWatcherBtn.querySelector('.btn-icon');

  if (isRunning) {
    watcherStatus.classList.add('running');
    statusText.textContent = '실행 중';
    toggleWatcherBtn.innerHTML = '<span class="btn-icon">■</span> 감시 중지';
  } else {
    watcherStatus.classList.remove('running');
    statusText.textContent = '중지됨';
    toggleWatcherBtn.innerHTML = '<span class="btn-icon">▶</span> 감시 시작';
  }
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  const toastMessage = toast.querySelector('.toast-message');
  const toastIcon = toast.querySelector('.toast-icon');

  toastMessage.textContent = message;
  toastIcon.textContent = type === 'success' ? '✓' : '✕';
  toast.className = `toast ${type} show`;

  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

// ==================== Event Handlers ====================

function handleSave() {
  if (!ruleName.value.trim()) {
    showToast('규칙 이름을 입력하세요', 'error');
    return;
  }

  if (!triggerPath.value.trim()) {
    showToast('감시 폴더 경로를 입력하세요', 'error');
    return;
  }

  const extensions = triggerExtensions.value
    .split(',')
    .map(ext => ext.trim())
    .filter(ext => ext.length > 0)
    .map(ext => ext.startsWith('.') ? ext : `.${ext}`);

  const ruleData = {
    name: ruleName.value.trim(),
    enabled: ruleEnabled.checked,
    trigger: {
      type: 'file_created',
      path: triggerPath.value.trim(),
      extensions: extensions
    },
    action: {
      type: actionType.value,
      output_path: outputPath.value.trim(),
      args: actionType.value === 'run_workflow' ? { workflow_name: workflowSelect.value } : {}
    }
  };

  saveRule(ruleData);
}

// ==================== Batch Processing ====================

let unprocessedFiles = [];

async function scanUnprocessedFiles() {
  if (!selectedRuleId) {
    showToast('먼저 규칙을 선택하세요', 'error');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/rules/${selectedRuleId}/scan`);
    const data = await response.json();

    if (data.success) {
      unprocessedFiles = data.unprocessed_files;

      if (unprocessedFiles.length === 0) {
        showToast('모든 파일이 이미 처리되었습니다', 'success');
        return;
      }

      // Show modal with file list and action type
      const modalBody = document.getElementById('modalBody');
      modalBody.innerHTML = `
        <p style="margin-bottom: 0.5rem; color: var(--text-secondary);">
          <strong>${data.count}개</strong>의 파일이 발견되었습니다.
        </p>
        <p style="margin-bottom: 1rem; color: var(--accent-primary); font-size: 0.9rem;">
          ⚡ 적용할 액션: <strong>${data.action_label}</strong>
        </p>
        ${unprocessedFiles.map(file => `
          <div class="file-item">
            <span class="file-item-name">📄 ${file.filename}</span>
            <span class="file-item-status">${file.status}</span>
          </div>
        `).join('')}
      `;

      document.getElementById('batchModal').style.display = 'flex';
    } else {
      showToast(data.error || '스캔 실패', 'error');
    }
  } catch (error) {
    showToast('스캔 중 오류가 발생했습니다', 'error');
    console.error('Error scanning files:', error);
  }
}

async function processAllFiles() {
  if (!selectedRuleId || unprocessedFiles.length === 0) return;

  try {
    const response = await fetch(`${API_BASE}/rules/${selectedRuleId}/process-all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        files: unprocessedFiles.map(f => f.filename)
      })
    });

    const data = await response.json();

    if (data.success) {
      showToast(`${data.processed}개 파일이 처리되었습니다`, 'success');
      closeModal();
    } else {
      showToast(data.error || '처리 실패', 'error');
    }
  } catch (error) {
    showToast('처리 중 오류가 발생했습니다', 'error');
    console.error('Error processing files:', error);
  }
}

function closeModal() {
  document.getElementById('batchModal').style.display = 'none';
  unprocessedFiles = [];
}

function showBatchSection() {
  const batchSection = document.getElementById('batchSection');
  if (batchSection) {
    batchSection.style.display = selectedRuleId ? 'block' : 'none';
  }
}

// ==================== Initialize ====================

document.addEventListener('DOMContentLoaded', () => {
  // Fetch initial data
  fetchRules();
  fetchWatcherStatus();
  fetchWorkflows();

  // Button handlers
  document.getElementById('addRuleBtn').addEventListener('click', showNewRuleForm);
  document.getElementById('cancelBtn').addEventListener('click', hideEditor);
  document.getElementById('saveBtn').addEventListener('click', handleSave);
  toggleWatcherBtn.addEventListener('click', toggleWatcher);

  // Action type change handler
  actionType.addEventListener('change', () => {
    workflowSelectContainer.style.display = actionType.value === 'run_workflow' ? 'block' : 'none';
  });

  // Batch processing handlers
  document.getElementById('scanFilesBtn')?.addEventListener('click', scanUnprocessedFiles);
  document.getElementById('closeModal')?.addEventListener('click', closeModal);
  document.getElementById('cancelBatchBtn')?.addEventListener('click', closeModal);
  document.getElementById('processBatchBtn')?.addEventListener('click', processAllFiles);

  // Poll watcher status every 5 seconds
  setInterval(fetchWatcherStatus, 5000);
});

