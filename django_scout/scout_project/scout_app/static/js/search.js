document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchResultsDropdown = document.getElementById('searchResultsDropdown');

    // check for input
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        // console.log('Search query:', query); // debug

        if (query.length >= 2) { // search if query >2
            fetch(`/scout_app/search/?query=${encodeURIComponent(query)}`, {
                headers: {
                    'Accept': 'application/json',
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Search results:', data); // Debugging log
                // remove old results
                searchResultsDropdown.innerHTML = '';

                if (data.players.length > 0) {
                    // append new results
                    data.players.forEach(player => {
                        const resultItem = document.createElement('a');
                        resultItem.className = 'dropdown-item';
                        resultItem.href = `/scout_app/player_dashboard/${player.id}/`;
                        resultItem.textContent = `${player.first_name} ${player.last_name} - ${player.position}`;
                        searchResultsDropdown.appendChild(resultItem);
                    });

                    // view all button
                    const viewAllButton = document.createElement('a');
                    viewAllButton.className = 'dropdown-item view-all-button';
                    viewAllButton.href = `/scout_app/search/?query=${encodeURIComponent(query)}`; // Redirect to full search page
                    viewAllButton.textContent = 'View All';
                    searchResultsDropdown.appendChild(viewAllButton);

                    // dropdown
                    searchResultsDropdown.classList.add('show');
                } else {
                    // no results
                    const noResults = document.createElement('span');
                    noResults.className = 'dropdown-item';
                    noResults.textContent = 'No players found';
                    searchResultsDropdown.appendChild(noResults);
                    searchResultsDropdown.classList.add('show');
                }
            })
            .catch(error => {
                console.error('Error fetching search results:', error);
            });
        } else {
            // no dropdown if 2< query
            searchResultsDropdown.classList.remove('show');
        }
    });

    // hide dropdown on focus loss
    document.addEventListener('click', function(event) {
        if (!event.target.closest('#searchForm')) {
            searchResultsDropdown.classList.remove('show');
        }
    });
});

