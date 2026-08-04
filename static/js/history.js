// GeoRisk Analysis History — fetches paginated results from /api/v1/analyses/

const container = document.getElementById("history-container");
const paginationControls = document.getElementById("pagination-controls");

const riskBadgeClass = {
    LOW: "bg-green-950 text-green-400 border-green-800",
    MODERATE: "bg-yellow-950 text-yellow-400 border-yellow-800",
    HIGH: "bg-red-950 text-red-400 border-red-800",
    INSUFFICIENT_DATA: "bg-slate-800 text-slate-400 border-slate-700",
};

function renderHistory(data) {
    const results = data.results || [];

    if (results.length === 0) {
        container.innerHTML = `<p class="text-slate-500 text-sm">No analyses yet. Draw a polygon on the Map Explorer to get started.</p>`;
        return;
    }

    container.innerHTML = results
        .map((item) => {
            const badgeClass = riskBadgeClass[item.flood_risk] || riskBadgeClass.INSUFFICIENT_DATA;
            const date = new Date(item.created_at).toLocaleString();

            return `
                <div class="bg-slate-900 border border-slate-800 rounded-lg p-4 flex items-center justify-between">
                    <div>
                        <div class="flex items-center gap-3">
                            <span class="text-xs px-2 py-1 rounded border ${badgeClass}">${item.flood_risk}</span>
                            <span class="text-sm text-slate-300">${item.area_km2} km²</span>
                        </div>
                        <p class="text-xs text-slate-500 mt-1">${date}</p>
                    </div>
                    <div class="text-right text-xs text-slate-400">
                        <p>Elevation: ${item.mean_elevation_m ?? "N/A"} m</p>
                        <p>Water coverage: ${item.water_coverage_percent}%</p>
                    </div>
                </div>
            `;
        })
        .join("");

    paginationControls.innerHTML = "";
    if (data.previous) {
        paginationControls.innerHTML += `<button onclick="loadHistory('${data.previous}')" class="px-3 py-1 text-sm bg-slate-800 rounded hover:bg-slate-700">Previous</button>`;
    }
    if (data.next) {
        paginationControls.innerHTML += `<button onclick="loadHistory('${data.next}')" class="px-3 py-1 text-sm bg-slate-800 rounded hover:bg-slate-700">Next</button>`;
    }
}

function loadHistory(url = "/api/v1/analyses/") {
    container.innerHTML = `<p class="text-slate-500 text-sm">Loading...</p>`;
    fetch(url)
        .then((res) => res.json())
        .then(renderHistory)
        .catch(() => {
            container.innerHTML = `<p class="text-red-400 text-sm">Could not load analysis history.</p>`;
        });
}

loadHistory();