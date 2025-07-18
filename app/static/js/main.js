document.addEventListener('DOMContentLoaded', () => {
	// Populate upcoming fights prediction list

	const list = document.getElementById('fight-list');
	list.innerHTML = '<li>Loading upcoming fights...</li>' // Create loading message on page load
  const fightData = [];

	fetch('/api/upcoming')
		.then(response => response.json())
		.then(data => {
			list.innerHTML = ''; // Clear the loading message
      fightData.push(...data)
			data.forEach(fight => {

				const li = document.createElement('li');
				li.className = "flex items-center gap-2 text-lg px-4 py-2 max-w-full overflow-x-auto font-sans font-bold";

				// Create spans for each fighter's name
				const fighterA = document.createElement('span');
				fighterA.textContent = fight.fighter_a_name;

				const vsText = document.createElement('span');
				vsText.textContent = ' vs ';

				const fighterB = document.createElement('span');
				fighterB.textContent = fight.fighter_b_name;
				//li.appendChild(beforePrediction);
				// Determine predicted winner by comparing prediction scores
				if (fight.prediction_a > fight.prediction_b) {
					fighterA.classList.add('text-green-600'); // winner color
					fighterB.classList.add('text-red-600'); // loser color
				} else if (fight.prediction_b > fight.prediction_a) {
					fighterB.classList.add('text-green-600');
					fighterA.classList.add('text-red-600');
				}

				const spacer = document.createElement('span');
				spacer.textContent = '--'

				// Append in order to li
				li.appendChild(fighterA);
				li.appendChild(vsText);
				li.appendChild(fighterB);
				li.appendChild(spacer)

				// Only add icon if no_odds is true
				let warningIcon = null;
				if (fight.no_odds) {
					warningIcon = document.createElement('img');
					warningIcon.src = '/static/icons/warning.svg';
					warningIcon.alt = 'Missing Odds';
					warningIcon.title = 'Odds were not available and defaulted to +100.';
					warningIcon.className = 'w-4 h-4 shrink-0';
					li.appendChild(warningIcon);
				}

				const predictionText = document.createElement('span');
				predictionText.textContent = `Prediction: ${(fight.prediction_a * 100).toFixed(2)}% - ${(fight.prediction_b * 100).toFixed(2)}% -- Odds to look for: ${fight.good_odds} ${fight.winner_last_name}`;


				li.appendChild(predictionText);
				list.appendChild(li);

				// Now we handle odds resubmission
				if (fight.no_odds) {
					// Create Edit Odds button
					const editBtn = document.createElement('button');
					editBtn.textContent = 'Edit Odds';
					// editBtn.style.marginLeft = '10px';
					editBtn.className = "px-3 py-1 ml-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition";
					li.appendChild(editBtn);

					editBtn.addEventListener('click', () => {
						// Remove button
						editBtn.remove();

						// Create input fields for odds
						const inputA = document.createElement('input');
						inputA.type = 'text';
						inputA.placeholder = 'Fighter A Odds';
						//inputA.style.width = '120px';
						//inputA.style.marginLeft = '10px';
						inputA.className = "w-30 px-2 py-1 ml-2 border border-gray-400 rounded placeholder-gray-500 text-sm";

						const inputB = document.createElement('input');
						inputB.type = 'text';
						inputB.placeholder = 'Fighter B Odds';
						//inputB.style.width = '120px';
						//inputB.style.marginLeft = '5px';
						inputB.className = "w-30 px-2 py-1 ml-2 border border-gray-400 rounded placeholder-gray-500 text-sm";

						// Create submit button
						const submitBtn = document.createElement('button');
						submitBtn.textContent = 'Submit';
						// submitBtn.style.marginLeft = '5px';
						submitBtn.className = "px-3 py-1 ml-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition";

						li.appendChild(inputA);
						li.appendChild(inputB);
						li.appendChild(submitBtn);

						submitBtn.addEventListener('click', () => {
							// Basic validation could be added here if you want

							// Show loading while waiting
							predictionText.textContent = 'Loading...';

							// Prepare data to send
							const postData = {
								fighter_a_id: fight.fighter_a_id,
								fighter_b_id: fight.fighter_b_id,
								fighter_a_odds: inputA.value,
								fighter_b_odds: inputB.value
							};

							fetch('/api/predict', {
									method: 'POST',
									headers: {
										'Content-Type': 'application/json'
									},
									body: JSON.stringify(postData)
								})
								.then(res => res.json())
								.then(updatedFight => {
                  // Update fightData
                  //console.log("fightData:", fightData);
                  //console.log("updatedFight:", updatedFight);

                  const index = fightData.findIndex(f =>
                    (f.fighter_a_name === updatedFight.fighter_a_name && f.fighter_b_name == updatedFight.fighter_b_name) ||
                    (f.fighter_a_name === updatedFight.fighter_b_name && f.fighter_b_name == updatedFight.fighter_a_name)
                  );

                  if (index !== -1) {
                    fightData[index] = updatedFight;

                    // Update .dataset.fight on all cards that use this fight
                    document.querySelectorAll('.bet-card').forEach(card => {
                      const stored = JSON.parse(card.dataset.fight || '{}');
                      const sameFight =
                        (stored.fighter_a_name === updatedFight.fighter_a_name && stored.fighter_b_name === updatedFight.fighter_b_name) ||
                        (stored.fighter_a_name === updatedFight.fighter_b_name && stored.fighter_b_name === updatedFight.fighter_a_name);
                    
                      if (sameFight) {
                        card.dataset.fight = JSON.stringify(updatedFight);
                      
                        // Recalculate prediction display
                        const fighter = card.querySelector('.fighter-select')?.value;
                        const oddsStr = card.querySelector('.odds-input')?.value?.trim();
                        const result = card.querySelector('.text-sm.font-semibold');
                      
                        if (!fighter || !oddsStr || !result) return;
                      
                        const prediction = fighter === updatedFight.fighter_a_name
                          ? updatedFight.prediction_a
                          : updatedFight.prediction_b;
                      
                        const odds = parseInt(oddsStr);
                        let decimalOdds = odds > 0 ? (odds / 100) + 1 : (100 / Math.abs(odds)) + 1;
                        const b = decimalOdds - 1;
                        const rawKelly = (b * prediction - (1 - prediction)) / b;
                        const safeFraction = Math.max(0, Math.min(rawKelly * 0.25, 1));
                      
                        if (safeFraction <= 0) {
                          result.textContent = "Don't bet, no value.";
                        } else {
                          result.textContent = `Bet ${(safeFraction * 100).toFixed(2)}% of your bankroll.`;
                        }
                      }
                    });
                  
                    console.log("Updated fight and recalculated bet text.");
                    updateEvRanking();
                  }

									// Update the line with new prediction & odds
									predictionText.textContent = `Prediction: ${(updatedFight.prediction_a * 100).toFixed(2)}% - ${(updatedFight.prediction_b * 100).toFixed(2)}% -- Odds to look for: ${updatedFight.good_odds} ${updatedFight.winner_last_name}`;
									// Remove old color classes if needed
									fighterA.classList.remove('text-green-600', 'text-red-600');
									fighterB.classList.remove('text-green-600', 'text-red-600');

									if (updatedFight.prediction_a > updatedFight.prediction_b) {
										fighterA.classList.add('text-green-600'); // winner color
										fighterB.classList.add('text-red-600'); // loser color
									} else if (updatedFight.prediction_b > updatedFight.prediction_a) {
										fighterB.classList.add('text-green-600');
										fighterA.classList.add('text-red-600');
									}

									inputA.remove();
									inputB.remove();
									submitBtn.remove();
									if (warningIcon) warningIcon.remove();
                  //fightSelect.dispatchEvent(new Event('change'));
								})
								.catch(err => {
									predictionText.textContent = 'Failed to update odds. Try again.';
									console.error(err);
								});
						});
					});
				}
        // Head-to-Head
        // Create head-to-head button
				const headToheadBtn = document.createElement('button');
				headToheadBtn.textContent = 'H2H';
				headToheadBtn.className = "px-3 py-1 ml-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition";
        li.appendChild(headToheadBtn);
        headToheadBtn.addEventListener('click', () => {
          const h2hInputData = new URLSearchParams({
            fighter_a_id: fight.fighter_a_id,
						fighter_b_id: fight.fighter_b_id
          });

          const url = `/api/head-to-head?${h2hInputData.toString()}`;

          fetch(url, {
								method: 'GET',
								headers: {
									'Content-Type': 'application/json'
								}
							})
            .then(response => response.json())
            .then(data => {
              const modal = document.getElementById('h2h-modal');
              const content = document.getElementById('h2h-content');
              const closeModalBtn = document.getElementById('closeModalBtn');
              closeModalBtn.addEventListener('click', () => {
                modal.classList.add('hidden');
              });
              content.innerHTML = ''; // Clear old content
              
              // Metadata block
              const metadataHTML = `
                <div class="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <h2 class="text-lg font-bold">${fight.fighter_a_name}</h2>
                    <p>Age: ${data.fighter_a_specs.metadata.age}</p>
                    <p>Height: ${data.fighter_a_specs.metadata.height}</p>
                    <p>Record: ${data.fighter_a_specs.metadata.wins} - ${data.fighter_a_specs.metadata.losses}</p>
                    <p>Reach: ${data.fighter_a_specs.metadata.reach}</p>
                  </div>
                  <div>
                    <h2 class="text-lg font-bold">${fight.fighter_b_name}</h2>
                    <p>Age: ${data.fighter_b_specs.metadata.age}</p>
                    <p>Height: ${data.fighter_b_specs.metadata.height}</p>
                    <p>Record: ${data.fighter_b_specs.metadata.wins} - ${data.fighter_b_specs.metadata.losses}</p>
                    <p>Reach: ${data.fighter_b_specs.metadata.reach}</p>
                  </div>
                </div>
              `;

              // Radar Chart Canvas
              const chartHtml = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div class="w-full max-w-md mx-auto" style="aspect-ratio: 1 / 1;">
                    <h2 class="text-lg font-bold text-center">Overall Rating: ${data.fighter_a_specs.overall}</h2>
                    <canvas id="radarChartA" width="300" height="300" class="w-full h-full block"></canvas>
                  </div>
                  <div class="w-full max-w-md mx-auto" style="aspect-ratio: 1 / 1;">
                    <h2 class="text-lg font-bold text-center">Overall Rating: ${data.fighter_b_specs.overall}</h2>
                    <canvas id="radarChartB" width="300" height="300" class="w-full h-full block"></canvas>
                  </div>
                </div>
              `;

              content.innerHTML = metadataHTML + chartHtml;
              modal.classList.remove('hidden');

              // Wait for canvas to render, then draw charts
              setTimeout(() => {
                const radarLabels = ['Striking', 'Grappling', 'Finish Threat', 'Durability', 'Recent Performance', 'Prestige'];
              
                new Chart(document.getElementById('radarChartA'), {
                  type: 'radar',
                  data: {
                    labels: radarLabels,
                    datasets: [{
                      label: fight.fighter_a_name,
                      data: [
                        data.fighter_a_specs.striking,
                        data.fighter_a_specs.grappling,
                        data.fighter_a_specs.finish_threat,
                        data.fighter_a_specs.durability,
                        data.fighter_a_specs.recent_performance,
                        data.fighter_a_specs.prestige
                      ],
                      backgroundColor: 'rgba(59, 130, 246, 0.2)',
                      borderColor: 'rgba(59, 130, 246, 1)',
                      pointBackgroundColor: 'rgba(59, 130, 246, 1)'
                    }]
                  },
                  options: { scales: { r: { min: 0, max: 100 } } }
                });
              
                new Chart(document.getElementById('radarChartB'), {
                  type: 'radar',
                  data: {
                    labels: radarLabels,
                    datasets: [{
                      label: fight.fighter_b_name,
                      data: [
                        data.fighter_b_specs.striking,
                        data.fighter_b_specs.grappling,
                        data.fighter_b_specs.finish_threat,
                        data.fighter_b_specs.durability,
                        data.fighter_b_specs.recent_performance,
                        data.fighter_b_specs.prestige
                      ],
                      backgroundColor: 'rgba(220, 38, 38, 0.2)',
                      borderColor: 'rgba(220, 38, 38, 1)',
                      pointBackgroundColor: 'rgba(220, 38, 38, 1)'
                    }]
                  },
                  options: { scales: { r: { min: 0, max: 100 } } }
                });
              }, 100); // slight delay to ensure canvases are in DO
            })
            .catch(error => {
              console.error('Error fetching head-to-head data:', error);
              alert('Failed to fetch head-to-head data.');
            });
        });

			});
      addBetCard(); // Create initial bet card
		})
		.catch(err => console.error('Failed to load upcoming fights:', err));


	// Handle betting sidebar logic
  const sidebarToggleBtn = document.getElementById('toggle-sidebar');
  const sidebarWrapper = document.getElementById('sidebar-wrapper');
	//const sidebar = document.getElementById('betting-sidebar');

  sidebarToggleBtn.addEventListener('click', () => {
    sidebarWrapper.classList.toggle('translate-x-full');
  });

  //const fightData = []; // Will store fetched fights
  const cardsContainer = document.getElementById('bet-cards');
  const addBetButton = document.getElementById('add-bet-card');

  // Fetch fight data once and reuse it
  // fetch('/api/upcoming')
  //   .then(res => res.json())
  //   .then(fights => {
  //     fightData.push(...fights); // Store for reuse
  //     addBetCard(); // Add the first card by default
  //   });

  addBetButton.addEventListener('click', addBetCard);

	function addBetCard() {
    const card = document.createElement('div');
    card.className = 'border-t border-gray-300 pt-4';
    card.classList.add('bet-card');
    
    // Fight select
    const fightSelect = document.createElement('select');
    fightSelect.className = 'w-full border px-2 py-1 mb-2 rounded';
    fightData.forEach(fight => {
      const opt = document.createElement('option');
      opt.value = JSON.stringify(fight);
      opt.textContent = `${fight.fighter_a_name} vs ${fight.fighter_b_name}`;
      fightSelect.appendChild(opt);
    });
    
    // Fighter select
    const fighterSelect = document.createElement('select');
    fighterSelect.className = 'w-full border px-2 py-1 mb-2 rounded';
    fighterSelect.classList.add('fighter-select');
    
    // Odds input
    const oddsInput = document.createElement('input');
    oddsInput.type = 'text';
    oddsInput.placeholder = 'Offered odds (e.g. +150)';
    oddsInput.className = 'w-full border px-2 py-1 mb-2 rounded';
    oddsInput.classList.add('odds-input');
    
    // Result display
    const result = document.createElement('div');
    result.className = 'text-sm font-semibold mt-2 text-blue-700';
    
    // Create a container for buttons
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'flex gap-2 mt-2';  // flex row with gap and margin top

    // Calculate button
    const calcBtn = document.createElement('button');
    calcBtn.textContent = 'Calculate';
    calcBtn.className = 'bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700';
    
    // Remove card button
    const removeBtn = document.createElement('button');
    removeBtn.textContent = 'Remove';
    removeBtn.className = 'bg-red-600 text-white px-4 py-1 rounded hover:bg-red-700';

    // Append buttons to container
    buttonsContainer.appendChild(calcBtn);
    buttonsContainer.appendChild(removeBtn);

    removeBtn.addEventListener('click', () => {
      card.remove(); // Assuming you saved the card container as `cardElement`
      updateEvRanking();    // Call your function to refresh rankings if needed
    });

    // Event: update fighter select when fight changes
    fightSelect.addEventListener('change', () => {
      const selected = JSON.parse(fightSelect.value);
      card.dataset.fight = fightSelect.value; // Save the selected fight on the card

      fighterSelect.innerHTML = '';

      [selected.fighter_a_name, selected.fighter_b_name].forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        fighterSelect.appendChild(opt);
      });

      // Default to predicted winner
      if (selected.prediction_a > selected.prediction_b) {
        fighterSelect.value = selected.fighter_a_name;
      } else {
        fighterSelect.value = selected.fighter_b_name;
      }
    });

    // Trigger initial update
    fightSelect.dispatchEvent(new Event('change'));

    // Event: calculate bet
    calcBtn.addEventListener('click', () => {
      const selected = JSON.parse(card.dataset.fight || '{}');
      const fighter = fighterSelect.value;
      const oddsStr = oddsInput.value.trim();
      if (!fighter || !oddsStr) {
        result.textContent = 'Please fill out all fields.';
        return;
      }

      const prediction = fighter === selected.fighter_a_name
        ? selected.prediction_a
        : selected.prediction_b;

      const odds = parseInt(oddsStr);
      let decimalOdds;
      if (odds > 0) decimalOdds = (odds / 100) + 1;
      else decimalOdds = (100 / Math.abs(odds)) + 1;

      const b = decimalOdds - 1;
      const rawKelly = (b * prediction - (1 - prediction)) / b;
      const safeFraction = Math.max(0, Math.min(rawKelly * 0.25, 1));

      if (safeFraction <= 0) {
        result.textContent = "Don't bet, no value.";
      } else {
        result.textContent = `Bet ${(safeFraction * 100).toFixed(2)}% of your bankroll.`;
      }

      updateEvRanking();
    });

    // Add elements to card
    card.appendChild(fightSelect);
    card.appendChild(fighterSelect);
    card.appendChild(oddsInput);
    card.appendChild(buttonsContainer);
    card.appendChild(result);

    cardsContainer.appendChild(card);
    fightSelect.dispatchEvent(new Event('change')); // trigger after append
  }

  // EV Ranking/Betting Order section
  function updateEvRanking() {
    const rankingContainer = document.getElementById('ranking-list');
    rankingContainer.innerHTML = ''; // Clear everything first
    
    const bankroll = parseFloat(document.getElementById('bankroll-input')?.value || '0');
    const cards = [...document.querySelectorAll('.bet-card')];
    
    const cascading = document.getElementById('cascading-bets')?.checked;
    const rounded = document.getElementById('bin-round-bets')?.checked;
    let availableBankroll = bankroll;
    
    const rawResults = [];
    
    // Step 1: Collect raw fractions
    cards.forEach(card => {
      const oddsStr = card.querySelector('.odds-input')?.value?.trim();
      const fighter = card.querySelector('.fighter-select')?.value;
      const fightData = JSON.parse(card.dataset.fight || '{}');
    
      if (!oddsStr || !fighter || !fightData.fighter_a_name || !fightData.fighter_b_name) return;
      const odds = parseInt(oddsStr);
      if (isNaN(odds)) return;
    
      let prediction;
      if (fighter === fightData.fighter_a_name) {
        prediction = fightData.prediction_a;
      } else if (fighter === fightData.fighter_b_name) {
        prediction = fightData.prediction_b;
      } else {
        return;
      }
    
      let decimalOdds = odds > 0 ? (odds / 100) + 1 : (100 / Math.abs(odds)) + 1;
      const b = decimalOdds - 1;
      const kellyFraction = (b * prediction - (1 - prediction)) / b;
      const safeFraction = Math.max(0, Math.min(kellyFraction, 1)) * 0.25;
    
      if (safeFraction <= 0 || isNaN(safeFraction)) return;
    
      rawResults.push({
        fight: `${fightData.fighter_a_name} vs ${fightData.fighter_b_name}`,
        fighter,
        fraction: safeFraction
      });
    });
  
    // Step 2: Calculate final bets using cascading/rounding
    const results = rawResults.map(entry => {
      let betAmount = 0;
    
      if (bankroll > 0) {
        const fraction = entry.fraction;
      
        betAmount = cascading ? availableBankroll * fraction : bankroll * fraction;
      
        if (rounded) {
          betAmount = round_wager(betAmount);
        }
      
        availableBankroll = Math.max(0, availableBankroll - betAmount);
      }
    
      return { ...entry, bet: betAmount };
    });
  
    // Step 3: Sort by final bet amount
    results.sort((a, b) => b.bet - a.bet);
  
    // Step 4: Render
    if (results.length === 0) {
      rankingContainer.innerHTML += `<p class="text-sm text-gray-500">No valid bets yet.</p>`;
      return;
    }
  
    results.forEach((entry, i) => {
      const line = document.createElement('div');
      line.className = 'flex justify-between text-sm';
      line.innerHTML = `
        <span>${i + 1}. ${entry.fighter}</span>
        <span>$${entry.bet.toFixed(2)}</span>
      `;
      rankingContainer.appendChild(line);
    });
  }

  const evToggleBtn = document.getElementById('toggle-ranking');
  const evRanking = document.getElementById('ev-ranking');

  let isCollapsed = false;

  evToggleBtn.addEventListener('click', () => {
    isCollapsed = !isCollapsed;

    if (isCollapsed) {
      // Collapse: just enough height for header
      evRanking.classList.remove('h-[30%]');
      evRanking.classList.add('h-[2.5rem]');
      evToggleBtn.textContent = 'Show';
    } else {
      // Expand to 30%
      evRanking.classList.remove('h-[2.5rem]');
      evRanking.classList.add('h-[30%]');
      evToggleBtn.textContent = 'Hide';
    }

    updateEvRanking()
  });

  // Settings Panel
  const settingsBtn = document.getElementById('settings-button');
  const settingsOverlay = document.getElementById('settings-overlay');
  const closeSettingsBtn = document.getElementById('close-settings');
  
  settingsBtn.addEventListener('click', () => {
    settingsOverlay.classList.remove('hidden');
  });
  
  closeSettingsBtn.addEventListener('click', () => {
    settingsOverlay.classList.add('hidden');
  });

  document.getElementById('cascading-bets').addEventListener('change', () => {
    updateEvRanking();
  });

  document.getElementById('bin-round-bets').addEventListener('change', () => {
    updateEvRanking();
  });

  updateEvRanking();
});

function round_wager(wager) {
  if (wager < 1) {
    if (wager > 0.5) return 1;
    else return 0;
  } else if (wager < 3) {
    return Math.round(wager * 2) / 2;
  } else if (wager < 20) {
    return Math.round(wager);
  } else if (wager < 100) {
    return Math.round(wager / 5) * 5;
  } else {
    return Math.round(wager / 10) * 10;
  }
}