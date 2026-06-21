let chart = null;
let allDocuments = [];
let categoryColors = {
    'contracts': '#FF5A5F',
    'employees': '#3CD070',
    'products': '#00F2FE',
    'company': '#FFD200',
    'general': '#A78BFA',
    'query': '#FFA000'
};

document.addEventListener('DOMContentLoaded', () => {
    loadDocuments();
    setupEventListeners();
});

function setupEventListeners() {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const clearSearchBtn = document.getElementById('clear-search-btn');

    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    clearSearchBtn.addEventListener('click', clearSearch);
}

async function loadDocuments() {
    try {
        const response = await fetch('/api/documents');
        if (!response.ok) throw new Error('Failed to fetch documents');
        
        allDocuments = await response.ok ? await response.json() : [];
        updateUIStats();
        initChart();
    } catch (error) {
        console.error('Error loading documents:', error);
        document.getElementById('doc-count').innerText = 'Error';
    }
}

function updateUIStats() {
    // Total Count
    document.getElementById('doc-count').innerText = allDocuments.length;
    
    // Category Counts
    const counts = { contracts: 0, employees: 0, products: 0, company: 0, general: 0 };
    allDocuments.forEach(doc => {
        const cat = doc.category;
        if (counts.hasOwnProperty(cat)) {
            counts[cat]++;
        } else {
            counts.general++;
        }
    });

    for (const [cat, count] of Object.entries(counts)) {
        const countEl = document.getElementById(`count-${cat}`);
        if (countEl) countEl.innerText = count;
    }
}

function initChart() {
    const ctx = document.getElementById('vector-chart').getContext('2d');
    
    // Group documents by category for separate datasets
    const categories = ['contracts', 'employees', 'products', 'company', 'general'];
    const datasets = categories.map(cat => {
        const docs = allDocuments.filter(d => d.category === cat);
        return {
            label: cat.charAt(0).toUpperCase() + cat.slice(1),
            data: docs.map(d => ({ x: d.x, y: d.y, docId: d.id })),
            backgroundColor: categoryColors[cat],
            pointRadius: 6,
            pointHoverRadius: 9,
            pointBorderWidth: 1,
            pointBorderColor: '#fff',
            showLine: false
        };
    });

    chart = new Chart(ctx, {
        type: 'scatter',
        data: { datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false // We use our own custom Legend UI
                },
                tooltip: {
                    backgroundColor: 'rgba(11, 15, 25, 0.95)',
                    titleFont: { family: 'Outfit', size: 14, weight: 'bold' },
                    bodyFont: { family: 'Inter', size: 12 },
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const rawData = context.raw;
                            const doc = allDocuments.find(d => d.id === rawData.docId);
                            if (doc) {
                                return [
                                    `Title: ${doc.filename}`,
                                    `Category: ${doc.category}`,
                                    `Coords: (${rawData.x.toFixed(2)}, ${rawData.y.toFixed(2)})`
                                ];
                            }
                            return `Query Coordinates: (${rawData.x.toFixed(2)}, ${rawData.y.toFixed(2)})`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#6B7280', font: { family: 'Inter', size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#6B7280', font: { family: 'Inter', size: 10 } }
                }
            },
            onClick: handleChartClick
        }
    });
}

function handleChartClick(event, elements) {
    if (!elements.length) return;
    
    const element = elements[0];
    const datasetIndex = element.datasetIndex;
    const index = element.index;
    const rawData = chart.data.datasets[datasetIndex].data[index];
    
    if (rawData.docId) {
        showDocumentDetails(rawData.docId);
    }
}

function showDocumentDetails(docId, distance = null) {
    const doc = allDocuments.find(d => d.id === docId);
    if (!doc) return;

    // Toggle states
    document.getElementById('details-empty-state').classList.add('hidden');
    const contentState = document.getElementById('details-content-state');
    contentState.classList.remove('hidden');

    // Populate Fields
    const categoryBadge = document.getElementById('details-category-badge');
    categoryBadge.innerText = doc.category;
    categoryBadge.className = `badge ${doc.category}`;

    document.getElementById('details-filename').innerText = doc.filename;
    document.getElementById('details-path').innerText = doc.source;
    document.getElementById('details-text').innerText = doc.content;

    const distanceContainer = document.getElementById('distance-container');
    if (distance !== null) {
        distanceContainer.classList.remove('hidden');
        document.getElementById('details-distance').innerText = distance.toFixed(4);
    } else {
        distanceContainer.classList.add('hidden');
    }

    // Highlight selected item in search results list (if visible)
    document.querySelectorAll('.result-item').forEach(item => {
        item.classList.remove('selected');
        if (item.dataset.id === docId) {
            item.classList.add('selected');
            item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    });
}

async function performSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, limit: 5 })
        });
        
        if (!response.ok) throw new Error('Search failed');
        const searchResults = await response.json();
        
        displaySearchResults(searchResults);
        updateChartWithQuery(searchResults);
    } catch (error) {
        console.error('Error during search:', error);
    }
}

function displaySearchResults(data) {
    const resultsCard = document.getElementById('results-card');
    const resultsList = document.getElementById('results-list');
    const clearBtn = document.getElementById('clear-search-btn');
    
    resultsList.innerHTML = '';
    resultsCard.classList.remove('hidden');
    clearBtn.classList.remove('hidden');

    if (data.matches.length === 0) {
        resultsList.innerHTML = '<div class="section-desc">No semantic matches found.</div>';
        return;
    }

    data.matches.forEach(match => {
        const item = document.createElement('div');
        item.className = 'result-item';
        item.dataset.id = match.id;
        item.innerHTML = `
            <div class="result-item-header">
                <span class="result-item-title">${match.filename}</span>
                <span class="result-item-distance"><i class="fa-solid fa-arrows-left-right"></i> ${match.distance.toFixed(3)}</span>
            </div>
            <div class="result-item-preview">${match.content}</div>
        `;
        
        item.addEventListener('click', () => {
            showDocumentDetails(match.id, match.distance);
        });
        
        resultsList.appendChild(item);
    });

    // Automatically display details of the top match
    if (data.matches.length > 0) {
        showDocumentDetails(data.matches[0].id, data.matches[0].distance);
    }
}

function updateChartWithQuery(data) {
    if (!chart) return;

    // 1. Remove any previous query or line datasets
    chart.data.datasets = chart.data.datasets.filter(ds => 
        ds.label !== 'Query' && !ds.isConnectorLine
    );

    // 2. Add query point dataset
    const queryX = data.query_x;
    const queryY = data.query_y;
    
    chart.data.datasets.push({
        label: 'Query',
        data: [{ x: queryX, y: queryY }],
        backgroundColor: categoryColors['query'],
        pointStyle: 'star',
        pointRadius: 12,
        pointHoverRadius: 14,
        pointBorderColor: '#fff',
        pointBorderWidth: 1.5,
        showLine: false
    });

    // 3. Add connector lines from query to matches
    data.matches.forEach(match => {
        chart.data.datasets.push({
            label: `To ${match.filename}`,
            data: [
                { x: queryX, y: queryY },
                { x: match.x, y: match.y }
            ],
            borderColor: 'rgba(255, 160, 0, 0.35)',
            borderWidth: 1.5,
            borderDash: [5, 5],
            pointRadius: 0,
            showLine: true,
            fill: false,
            isConnectorLine: true // tag it so we can easily filter it out next time
        });
    });

    chart.update();
}

function clearSearch() {
    document.getElementById('search-input').value = '';
    document.getElementById('results-card').classList.add('hidden');
    document.getElementById('clear-search-btn').classList.add('hidden');
    
    // Hide details content, restore empty state
    document.getElementById('details-content-state').classList.add('hidden');
    document.getElementById('details-empty-state').classList.remove('hidden');

    if (chart) {
        // Remove query and lines
        chart.data.datasets = chart.data.datasets.filter(ds => 
            ds.label !== 'Query' && !ds.isConnectorLine
        );
        chart.update();
    }
}
