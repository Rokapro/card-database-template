const searchBar = document.querySelector(".searchBar");
const cardRow = document.getElementById("cardRow");
const noResults = document.getElementById("noResults");
const totalCardCount = document.getElementById("totalCardCount");
const sortDropdown = document.getElementById("sortDropdown");

const typeFiltersContainer = document.getElementById("typeFilters");
const setFiltersContainer = document.getElementById("setFilters");
const domainFiltersContainer = document.getElementById("domainFilters");

let allCards = [];
let activeSort = "name_asc";
let activeTypeFilters = new Set();
let activeSetFilters = new Set();
let activeDomainFilters = new Set();

// Rarity order for sorting
const RARITY_ORDER = {
	"common": 1,
	"uncommon": 2,
	"rare": 3,
	"epic": 4,
	"legendary": 5,
	"legend": 6,
	"promo": 7,
	"showcase": 8,
};

fetch("riftbound/cards.csv")
	.then((response) => response.text())
	.then((csvText) => {
		allCards = parseCSV(csvText);
		populateFilters(allCards);
		renderCards(allCards);
		updateTotalCardCount(allCards);
	})
	.catch((error) => {
		console.error("Error loading CSV:", error);
	});

function parseCSV(csvText) {
	const lines = csvText.trim().split(/\r?\n/);
	const headers = lines[0].split(",").map((header) => header.trim());

	return lines.slice(1).map((line) => {
		const values = line.split(",");
		const card = {};

		headers.forEach((header, index) => {
			card[header] = values[index]?.trim() || "";
		});

		card.altArt = (card.altArt || "false").toLowerCase() === "true";
		card.overnumbered = (card.overnumbered || "false").toLowerCase() === "true";
		card.isPromo = (card.isPromo || "false").toLowerCase() === "true"; // Parse isPromo
		card.collector_number = parseInt(card.collector_number, 10) || 0;


		return card;
	});
}

function populateFilters(cards) {
    const types = new Set();
    const sets = new Set();
    const domains = new Set();

    cards.forEach(card => {
        if (card.type) types.add(card.type.trim());
        if (card.set) sets.add(card.set.trim());
        if (card.color) {
            card.color.split('&').forEach(d => domains.add(d.trim()));
        }
    });

    populateFilterColumn(typeFiltersContainer, Array.from(types).sort(), activeTypeFilters, 'type');
    populateFilterColumn(setFiltersContainer, Array.from(sets).sort(), activeSetFilters, 'set');
    populateFilterColumn(domainFiltersContainer, Array.from(domains).sort(), activeDomainFilters, 'domain');
}

function populateFilterColumn(container, items, activeFilterSet, groupName) {
    container.innerHTML = items.map(item => `
        <div class="form-check">
            <input class="form-check-input" type="checkbox" value="${item}" id="${groupName}-${item}" data-group="${groupName}">
            <label class="form-check-label" for="${groupName}-${item}">
                ${item}
            </label>
        </div>
    `).join('');

    container.querySelectorAll('.form-check-input').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                activeFilterSet.add(e.target.value);
            } else {
                activeFilterSet.delete(e.target.value);
            }
            renderCards(allCards);
        });
    });
}


function renderCards(cards) {
	const filteredCards = cards.filter((card) => {
		const searchText = searchBar.value.toLowerCase().trim();

		const matchesSearch = searchText === "" ||
			`${card.name} ${card.set} ${card.type} ${card.color} ${card.altArt ? "alt art" : ""} ${card.overnumbered ? "overnumbered" : ""} ${card.isPromo ? "promo" : ""}`.toLowerCase().includes(searchText);

        const matchesType = activeTypeFilters.size === 0 || activeTypeFilters.has(card.type);
        const matchesSet = activeSetFilters.size === 0 || activeSetFilters.has(card.set);
        const cardDomains = new Set((card.color || "").split('&'));
        const matchesDomain = activeDomainFilters.size === 0 || [...activeDomainFilters].some(df => cardDomains.has(df));

		return matchesSearch && matchesType && matchesSet && matchesDomain;
	});

	const sortedCards = sortCards(filteredCards, activeSort);

	if (sortedCards.length === 0) {
		cardRow.innerHTML = "";
		noResults.style.display = "block";
		return;
	}

	noResults.style.display = "none";

	cardRow.innerHTML = sortedCards.map((card) => {
		const flags = [];
		if (card.altArt) flags.push("Alt Art");
		if (card.overnumbered) flags.push("Overnumbered");
		if (card.isPromo) flags.push("Promo"); // Display Promo flag

		return `
      <div class="col-6 col-md-4 col-lg-3 card-wrapper"
           data-name="${card.name.toLowerCase()}"
           data-set="${card.set.toLowerCase()}"
           data-type="${card.type.trim().toLowerCase()}"
           data-color="${(card.color || "").toLowerCase()}">
        <div class="card-custom">
          <img src="riftbound-images/${card.image}" class="card-img${(card.type||'').trim().toLowerCase() === 'battlefield' ? ' rotate-90' : ''}" alt="${card.name}">
        </div>
        <div class="card-caption">
          <strong>${card.name}</strong><br>
          Quantity: ${card.quantity}<br>
          Type: ${card.type}${flags.length ? `<br>${flags.join(" | ")}` : ""}
        </div>
      </div>
    `;
	}).join("");
}

function sortCards(cards, sortBy) {
    const [sortField, sortOrder] = sortBy.split('_');
	const sorted = [...cards];

	sorted.sort((a, b) => {
		let valA, valB;

		switch (sortField) {
			case 'name':
				valA = a.name;
				valB = b.name;
				return valA.localeCompare(valB);
			case 'collector_number':
				valA = a.collector_number;
				valB = b.collector_number;
				return valA - valB;

			case 'rarity':
				let rarityA = a.isPromo ? "promo" : a.rarity.toLowerCase();
				let rarityB = b.isPromo ? "promo" : b.rarity.toLowerCase();
				valA = RARITY_ORDER[rarityA] || 99;
				valB = RARITY_ORDER[rarityB] || 99;
				return valA - valB;
			default:
				return 0;
		}
	});

	if (sortOrder === 'desc') {
		sorted.reverse();
	}

	return sorted;
}


function updateTotalCardCount(cards) {
	const total = cards.reduce((sum, card) => {
		const qty = parseInt(card.quantity, 10);
		return sum + (isNaN(qty) ? 0 : qty);
	}, 0);

	totalCardCount.textContent = `Total Cards: ${total}`;
}

searchBar.addEventListener("input", () => {
	renderCards(allCards);
});

sortDropdown.addEventListener("change", (e) => {
	activeSort = e.target.value;
	renderCards(allCards);
});