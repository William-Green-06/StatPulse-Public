var fighter_a_id = -1;
var fighter_b_id = -1;

async function searchFighters(query, fighterNumber) {
  const suggestions = document.getElementById(`fighter${fighterNumber}-suggestions`);
  const input = document.getElementById(`fighter${fighterNumber}-name`);

  if (!query) {
    suggestions.classList.add('hidden');
    suggestions.innerHTML = '';
    return;
  }

  try {
    const response = await fetch(`/api/fighter-search?q=${encodeURIComponent(query)}`);
    const fighters = await response.json();

    if (fighters.length === 0) {
      suggestions.classList.add('hidden');
      suggestions.innerHTML = '';
      return;
    }

    suggestions.innerHTML = fighters
      .map(f => `<li class="cursor-pointer px-3 py-2 hover:bg-blue-100" onclick="selectFighter(${fighterNumber}, '${f.name.replace(/'/g, "\\'")}', ${f.id})">${f.name}</li>`)
      .join('');
    suggestions.classList.remove('hidden');
  } catch (err) {
    console.error('Search error:', err);
    suggestions.classList.add('hidden');
  }
}

// Prevent id's from changing if the name is changed
document.getElementById('fighter1-name').addEventListener('input', () => {
  fighter_a_id = -1; // reset on manual input change
});
document.getElementById('fighter2-name').addEventListener('input', () => {
  fighter_b_id = -1;
});

function selectFighter(fighterNumber, name, id) {
  const input = document.getElementById(`fighter${fighterNumber}-name`);
  const suggestions = document.getElementById(`fighter${fighterNumber}-suggestions`);

  input.value = name;
  suggestions.classList.add('hidden');

  if (fighterNumber === 1) {
    fighter_a_id = id;
  } else if (fighterNumber === 2) {
    fighter_b_id = id;
  }
}

// Handle predict button
document.getElementById('predict-button').addEventListener('click', () => {
  const output = document.getElementById('predict-output');
  output.textContent = ''; // Clear previous results

  //define fighter names for output
  fighter_a_name = document.getElementById('fighter1-name').value.trim();
  fighter_b_name = document.getElementById('fighter2-name').value.trim();
  
  // Prepare the payload — adjust fields as your API expects
  const payload = {
    fighter_a_id: fighter_a_id,
	fighter_b_id: fighter_b_id,
	fighter_a_odds: '100',
	fighter_b_odds: '100'
  };

  // Call your predict API endpoint (adjust URL as needed)
  fetch('/api/predict', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload),
  })
    .then(res => res.json())
    .then(data => {
      // Adjust this formatting based on your prediction response format
      output.classList.remove('text-red-600');
      output.innerHTML = `
        <p><strong>${fighter_a_name}</strong>: ${(data.prediction_a * 100).toFixed(2)}%</p>
        <p><strong>${fighter_b_name}</strong>: ${(data.prediction_b * 100).toFixed(2)}%</p>
      `;
    })
    .catch(err => {
      console.error('Prediction API error:', err);
      output.textContent = 'Error making prediction. Please check your input.';
      output.classList.add('text-red-600');
    });
});