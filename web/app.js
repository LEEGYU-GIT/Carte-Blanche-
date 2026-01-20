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
    
    showEditor();
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
      output_path: outputPath.value.trim()
    }
  };
  
  saveRule(ruleData);
}

// ==================== Initialize ====================

document.addEventListener('DOMContentLoaded', () => {
  // Fetch initial data
  fetchRules();
  fetchWatcherStatus();
  
  // Button handlers
  document.getElementById('addRuleBtn').addEventListener('click', showNewRuleForm);
  document.getElementById('cancelBtn').addEventListener('click', hideEditor);
  document.getElementById('saveBtn').addEventListener('click', handleSave);
  toggleWatcherBtn.addEventListener('click', toggleWatcher);
  
  // Poll watcher status every 5 seconds
  setInterval(fetchWatcherStatus, 5000);
});
