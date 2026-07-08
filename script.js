const searchBar = document.querySelector(".searchBar");
const cardRow = document.getElementById("cardRow");
const noResults = document.getElementById("noResults");
const totalCardCount = document.getElementById("totalCardCount");
const filterButtons = document.querySelectorAll(".filter-button");
const sortBy = document.getElementById("sortBy");
const sortOrderSelect = document.getElementById("sortOrder");

let allCards = [];
let activeFilter = "All";
let activeSort = "name";
let sortOrder = "asc";

fetch("riftbound/cards.csv")
  .then((response) => response.text())
  .then((csvText) => {
    allCards = parseCSV(csvText);
    renderCards(allCards);
    updateTotalCardCount(allCards);
  })
  .catch((error) => {
    console.error("Error loading CSV:", error);
  });

function parseCSV(csvText) {
  const lines = csvText.trim().split("\n");
  const headers = lines[0].split(",").map((header) => header.trim());

  return lines.slice(1).map((line) => {
    const values = line.split(",");
    const card = {};

    headers.forEach((header, index) => {
      card[header] = values[index]?.trim() || "";
    });

    card.altArt = (card.altArt || "false").toLowerCase() === "true";
    card.overnumbered = (card.overnumbered || "false").toLowerCase() === "true";

    return card;
  });
}

function renderCards(cards) {
  const filteredCards = cards.filter((card) => {
    const matchesType = activeFilter === "All" || card.type.trim().toLowerCase() === activeFilter.toLowerCase();
    const searchText = searchBar.value.toLowerCase().trim();

    const matchesSearch = searchText === "" ||
      `${card.name} ${card.set} ${card.type} ${card.color} ${card.altArt ? "alt art" : ""} ${card.overnumbered ? "overnumbered" : ""}`.toLowerCase().includes(searchText);

    return matchesType && matchesSearch;
  });

  const sortedCards = sortCards(filteredCards, activeSort, sortOrder);

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

function sortCards(cards, sortBy, order) {
  const sorted = [...cards];

  if (sortBy === 'name') {
    sorted.sort((a, b) => a.name.localeCompare(b.name));
  } else if (sortBy === 'rarity') {
    // To be implemented once rarity data is available
  } else {
    // Default sorting if no active filter
    if (activeFilter === "All") {
        const typePriority = {
          legend: 1,
          unit: 2,
          spell: 3,
          rune: 4,
          gear: 5,
          battlefield: 6,
          token: 7,
        };
    
        return [...cards].sort((a, b) => {
          const colorA = (a.color || "").split("&")[0].trim().toLowerCase();
          const colorB = (b.color || "").split("&")[0].trim().toLowerCase();
          if (colorA !== colorB) {
            return colorA.localeCompare(colorB);
          }
    
          const typeA = (a.type || "").trim().toLowerCase();
          const typeB = (b.type || "").trim().toLowerCase();
          const priorityA = typePriority[typeA] ?? 99;
          const priorityB = typePriority[typeB] ?? 99;
          if (priorityA !== priorityB) {
            return priorityA - priorityB;
          }
    
          return a.name.localeCompare(b.name);
        });
      }
  }

  if (order === 'desc') {
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

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    filterButtons.forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");
    activeFilter = button.getAttribute("data-filter");
    renderCards(allCards);
  });
});

sortBy.addEventListener("change", (e) => {
    activeSort = e.target.value;
    renderCards(allCards);
});

sortOrderSelect.addEventListener("change", (e) => {
    sortOrder = e.target.value;
    renderCards(allCards);
});

