// GeoRisk Map Explorer — Leaflet + Draw + API integration

const CENTER = [26.14, 91.73]; // Guwahati, Assam
const map = L.map("map").setView(CENTER, 12);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
}).addTo(map);

// Layer group for drawn/result geometry
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

const drawControl = new L.Control.Draw({
    edit: { featureGroup: drawnItems },
    draw: {
        polygon: true,
        rectangle: true,
        polyline: false,
        circle: false,
        marker: false,
        circlemarker: false,
    },
});
map.addControl(drawControl);

const loadingIndicator = document.getElementById("loading-indicator");
const analysisPanel = document.getElementById("analysis-panel");

function showLoading(isLoading) {
    loadingIndicator.classList.toggle("hidden", !isLoading);
}

function renderAnalysisResult(result) {
    if (result.error) {
        analysisPanel.innerHTML = `
            <div class="bg-red-950 border border-red-800 text-red-300 rounded-md p-3 text-sm">
                ${result.error}
            </div>`;
        return;
    }

    const riskColors = {
        LOW: "text-green-400 bg-green-950 border-green-800",
        MODERATE: "text-yellow-400 bg-yellow-950 border-yellow-800",
        HIGH: "text-red-400 bg-red-950 border-red-800",
        INSUFFICIENT_DATA: "text-slate-400 bg-slate-800 border-slate-700",
    };
    const riskClass = riskColors[result.flood_risk] || "text-slate-400 bg-slate-800 border-slate-700";

    analysisPanel.innerHTML = `
        <div class="border ${riskClass} rounded-md px-3 py-2 text-center font-semibold">
            Flood Risk: ${result.flood_risk}
        </div>
        <div class="grid grid-cols-2 gap-3 mt-3 text-slate-300">
            <div>
                <p class="text-xs text-slate-500">Area</p>
                <p class="font-medium">${result.area_km2} km²</p>
            </div>
            <div>
                <p class="text-xs text-slate-500">Mean Elevation</p>
                <p class="font-medium">${result.mean_elevation_m ?? "N/A"} m</p>
            </div>
            <div>
                <p class="text-xs text-slate-500">Water Coverage</p>
                <p class="font-medium">${result.water_coverage_percent}%</p>
            </div>
            <div>
                <p class="text-xs text-slate-500">Water Bodies</p>
                <p class="font-medium">${result.water_bodies_intersecting}</p>
            </div>
            <div class="col-span-2">
                <p class="text-xs text-slate-500">Population Exposed (est.)</p>
                <p class="font-medium">${result.population_exposed.toLocaleString()}</p>
            </div>
        </div>
    `;
}

function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : "";
}

async function submitAnalysis(geojsonGeometry) {
    showLoading(true);
    analysisPanel.innerHTML = "";

    try {
        const response = await fetch("/api/v1/analysis/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({ geometry: geojsonGeometry }),
        });

        const data = await response.json();

        if (!response.ok) {
            renderAnalysisResult({ error: data.error || "Analysis failed. Please try a smaller or valid polygon." });
            return;
        }

        renderAnalysisResult(data);
    } catch (err) {
        renderAnalysisResult({ error: "Network error — could not reach the analysis API." });
    } finally {
        showLoading(false);
    }
}

map.on(L.Draw.Event.CREATED, function (event) {
    drawnItems.clearLayers(); // one active polygon at a time for this MVP
    const layer = event.layer;
    drawnItems.addLayer(layer);

    const geojson = layer.toGeoJSON().geometry;
    submitAnalysis(geojson);
});

// Load available layers into the left panel (Phase 8 will render them on the map)
fetch("/api/v1/layers/")
    .then((res) => res.json())
    .then((data) => {
        const container = document.getElementById("layer-controls");
        const layers = data.results || data;
        if (!layers.length) {
            container.innerHTML = `<p class="text-slate-500 text-xs">No layers configured yet.</p>`;
            return;
        }
        container.innerHTML = layers
            .map(
                (layer) => `
                <label class="flex items-center gap-2">
                    <input type="checkbox" checked class="accent-blue-500" />
                    ${layer.name}
                </label>`
            )
            .join("");
    })
    .catch(() => {
        document.getElementById("layer-controls").innerHTML =
            `<p class="text-red-400 text-xs">Could not load layers.</p>`;
    });