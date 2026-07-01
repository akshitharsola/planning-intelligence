function renderBarChart(canvasId, data, label) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.map((row) => row.label),
      datasets: [{ label, data: data.map((row) => row.value) }],
    },
  });
}

document.addEventListener("DOMContentLoaded", () => {
  renderBarChart("monthly-chart", monthlyData, "Applications received per month");
  renderBarChart("status-chart", statusData, "Applications by status");
  renderBarChart("type-chart", typeData, "Applications by type");
});
