let activeFighterId = null;

async function editFighter(fighterId) {
    // If the same fighter is clicked, toggle it closed
    if (activeFighterId === fighterId) {
        closeFighterDetails(fighterId);
        activeFighterId = null;
        return;
    }

    // Close previous if there was one
    if (activeFighterId !== null) {
        closeFighterDetails(activeFighterId);
    }

    const detailsDiv = document.getElementById(`details-${fighterId}`);
    const button = document.querySelector(`[onclick="editFighter('${fighterId}')"]`);

    // Fetch fighter data
    const res = await fetch(`/api/fighter-data?q=${fighterId}`);
    if (!res.ok) {
        detailsDiv.innerHTML = '<p class="text-red-500">Error loading fighter data.</p>';
        return;
    }
    const fighter = await res.json();

    // Fill details
    detailsDiv.innerHTML = Object.entries(fighter).map(([key, value]) => `
      <div class="flex items-center gap-2 bg-gray-50 p-2 rounded border border-gray-200">
          <span class="font-semibold capitalize">${key}:</span>
          <input 
              type="text"
              id="stat-${fighterId}-${key}"
              value="${value}"
              class="bg-gray-200 px-2 py-1 rounded border border-gray-300 flex-1"
              disabled
          />
          <button id="edit-btn-${fighterId}-${key}"
                  class="px-2 py-1 bg-yellow-500 hover:bg-yellow-600 rounded text-white"
                  onclick="enableEdit('${fighterId}', '${key}')">
              ✏️
          </button>
          <div id="edit-actions-${fighterId}-${key}" class="hidden flex gap-1">
              <button class="px-2 py-1 bg-blue-500 hover:bg-blue-600 rounded text-white"
                      onclick="saveEdit('${fighterId}', '${key}')">
                  💾 Save
              </button>
              <button class="px-2 py-1 bg-red-500 hover:bg-red-600 rounded text-white"
                      onclick="cancelEdit('${fighterId}', '${key}')">
                  ❌ Cancel
              </button>
          </div>
      </div>
    `).join('');


    // Show details and set button active
    detailsDiv.classList.remove('hidden');
    button.classList.add('bg-blue-800'); // darker color for active
    activeFighterId = fighterId;
}

function closeFighterDetails(fighterId) {
    const detailsDiv = document.getElementById(`details-${fighterId}`);
    const button = document.querySelector(`[onclick="editFighter('${fighterId}')"]`);
    if (detailsDiv) {
        detailsDiv.classList.add('hidden');
        detailsDiv.innerHTML = '';
    }
    if (button) {
        button.classList.remove('bg-blue-800'); // remove active color
    }
}

function enableEdit(fighterId, key) {
    const input = document.getElementById(`stat-${fighterId}-${key}`);
    input.dataset.originalValue = input.value;
    input.disabled = false;
    input.classList.remove('bg-gray-200');

    document.getElementById(`edit-btn-${fighterId}-${key}`).classList.add('hidden');
    document.getElementById(`edit-actions-${fighterId}-${key}`).classList.remove('hidden');
}

function cancelEdit(fighterId, key) {
    const input = document.getElementById(`stat-${fighterId}-${key}`);
    input.value = input.dataset.originalValue;
    input.disabled = true;
    input.classList.add('bg-gray-200');

    document.getElementById(`edit-btn-${fighterId}-${key}`).classList.remove('hidden');
    document.getElementById(`edit-actions-${fighterId}-${key}`).classList.add('hidden');
}

async function saveEdit(fighterId, key) {
    const input = document.getElementById(`stat-${fighterId}-${key}`);
    const newValue = input.value;

    try {
        const res = await fetch(`/api/set-fighter-stat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id: fighterId,
                field: key,
                value: newValue
            })
        });

        if (!res.ok) {
            throw new Error(`Failed to update fighter: ${res.status}`);
        }

        // Success — lock input but keep new value
        input.disabled = true;
        input.classList.add('bg-gray-200');

        document.getElementById(`edit-btn-${fighterId}-${key}`).classList.remove('hidden');
        document.getElementById(`edit-actions-${fighterId}-${key}`).classList.add('hidden');

    } catch (err) {
        alert('Error saving change: ' + err.message);
        // Optionally restore original value if save failed
        input.value = input.dataset.originalValue;
        cancelEdit(fighterId, key);
    }
}



function restorePencil(fighterId, key) {
    const container = document.getElementById(`stat-${fighterId}-${key}`).parentElement;
    container.querySelectorAll('button').forEach(btn => btn.remove());
    container.insertAdjacentHTML('beforeend', `
        <button class="px-2 py-1 bg-yellow-500 rounded text-white" 
                onclick="enableEdit('${fighterId}', '${key}')">✏️</button>
    `);
}

// UI Tabs
function showTab(tabName) {
  const tabs = ['fighters', 'commands'];

  tabs.forEach(name => {
    // Toggle content
    document.getElementById(`content-${name}`).classList.add('hidden');
    // Toggle tab button styles
    const btn = document.getElementById(`tab-${name}`);
    if (name === tabName) {
      document.getElementById(`content-${name}`).classList.remove('hidden');
      btn.classList.remove('bg-gray-100', 'text-gray-700', 'border-transparent');
      btn.classList.add('bg-indigo-600', 'text-white', 'border-indigo-600');
    } else {
      btn.classList.add('bg-gray-100', 'text-gray-700', 'border-transparent');
      btn.classList.remove('bg-indigo-600', 'text-white', 'border-indigo-600');
    }
  });
}

// Run a command from the backend
async function runCommand(commandName) {
    if (!confirm(`Run command: ${commandName}?`)) return;

    const container = document.querySelector(`[data-command="${commandName}"]`);
    let args = [];

    if (container) {
        const inputs = container.querySelectorAll('.arg');
        args = Array.from(inputs).map(i => i.value).filter(v => v !== ''); // ignore empty
    }

    try {
        const res = await fetch(`/api/run-command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: commandName, args })
        });

        const data = await res.json();

        if (!res.ok) {
            alert(`Failed: ${data.error || 'Unknown error'}`);
        } else {
            alert(`Success: ${data.message}`);
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
}
