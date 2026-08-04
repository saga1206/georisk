// GeoRisk Dashboard — fetches /api/v1/stats/ and renders summary UI

const riskBadgeClass = {
    LOW: "bg-green-950 text-green-400 border-green-800",
    MODERATE: "bg-yellow-950 text-yellow-400 border-yellow-800",
    HIGH: "bg-red-950 text-red-400 border-red-800",
    INSUFFICIENT_DATA: "bg-slate-800 text-slate-400 border-slate-700",
};

const riskBarColor = {
    LOW: "bg-green-500",
    MODERATE: "bg-yellow-500",
    HIGH: "bg-red-500",
    INSUFFICIENT_DATA: "bg-slate-500",
};

function renderSummaryCards(data) {
    const cards = [
        { label: "Total Analyses", value: data.total_analyses },
        { label: "Avg. Area Analyzed", value: `${data.average_area_km2} km²` },
        { label: "Population Exposed (cum.)", value: data.total_population_exposed.toLocaleString() },
        { label: "Water Bodies Loaded", value: data.water_bodies_loaded.toLocaleString() },
    ];

    document.getElementById("summary-cards").innerHTML = cards
        .map(
            (card) => `
            <div class="bg-slate-900 border border-slate-800 rounded-lg p-4">
                <p class="text-xs text-slate-500">${card.label}</p>
                <p class="text-2xl font-bold mt-1">${card.value}</p>
            </div>`
        )
        .join("");
}

function renderRiskBreakdown(breakdown) {
    const total = Object.values(breakdown).reduce((a, b) => a + b, 0);
    const container = document.getElementById("risk-breakdown");

    if (total === 0) {
        container.innerHTML = `<p class="text-slate-500 text-sm">No analyses run yet.</p>`;
        return;
    }

    container.innerHTML = Object.entries(breakdown)
        .map(([risk, count]) => {
            const percent = total ? Math.round((count / total) * 100) : 0;
            return `
                <div>
                    <div class="flex justify-between text-xs mb-1">
                        <span class="px-2 py-0.5 rounded border ${riskBadgeClass[risk]}">${risk}</span>
                        <span class="text-slate-400">${count} (${percent}%)</span>
                    </div>
                    <div class="w-full bg-slate-800 rounded-full h-1.5">
                        <div class="${riskBarColor[risk]} h-1.5 rounded-full" style="width: ${percent}%"></div>
                    </div>
                </div>
            `;
        })
        .join("");
}

function renderRecentAnalyses(analyses) {
    const container = document.getElementById("recent-analyses");

    if (analyses.length === 0) {
        container.innerHTML = `<p class="text-slate-500 text-sm">No analyses yet. Start by drawing a polygon on the Map Explorer.</p>`;
        return;
    }

    container.innerHTML = analyses
        .map((item) => {
            const badgeClass = riskBadgeClass[item.flood_risk] || riskBadgeClass.INSUFFICIENT_DATA;
            const date = new Date(item.created_at).toLocaleDateString();
            return `
                <div class="flex items-center justify-between border-b border-slate-800 last:border-0 py-2">
                    <div class="flex items-center gap-3">
                        <span class="text-xs px-2 py-0.5 rounded border ${badgeClass}">${item.flood_risk}</span>
                        <span class="text-sm text-slate-300">${item.area_km2} km²</span>
                    </div>
                    <span class="text-xs text-slate-500">${date}</span>
                </div>
            `;
        })
        .join("");
}

fetch("/api/v1/stats/")
    .then((res) => res.json())
    .then((data) => {
        renderSummaryCards(data);
        renderRiskBreakdown(data.risk_breakdown);
        renderRecentAnalyses(data.recent_analyses);
    })
    .catch(() => {
        document.getElementById("summary-cards").innerHTML =
            `<p class="text-red-400 text-sm col-span-4">Could not load dashboard stats.</p>`;
    });