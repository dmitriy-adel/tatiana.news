function updateTextStats(data) {
    const map = {
        'total_news': 'total_news',
        'total_sources': 'total_sources',
        'total_users': 'total_users',
        'most_popular_source': 'most_popular_source'
    };
    Object.keys(map).forEach(key => {
        const el = document.getElementById(map[key]);
        if (el && data[key] !== undefined) el.textContent = data[key];
    });
}

function renderPieChart(data) {
    const ctx = document.getElementById('pieChart');
    if (!ctx) return;
    if (pieChartInstance) { pieChartInstance.destroy(); pieChartInstance = null; }

    const labels = Object.keys(data);
    const values = Object.values(data);
    const colors = labels.map((_, i) => chartColors[i % chartColors.length]);

    pieChartInstance = new Chart(ctx, {
        type: 'pie',
        data: { labels, datasets: [{ data: values, backgroundColor: colors, borderColor: '#fff', borderWidth: 3, hoverOffset: 18 }] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { padding: 18, usePointStyle: true } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((ctx.raw / total) * 100).toFixed(1);
                            return `${ctx.label}: ${ctx.raw} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderBarChart(data) {
    const ctx = document.getElementById('barChart');
    if (!ctx) return;
    if (barChartInstance) { barChartInstance.destroy(); barChartInstance = null; }

    const labels = Object.keys(data);
    const values = Object.values(data);

    barChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Количество новостей',
                data: values,
                backgroundColor: '#3b82f6',
                borderRadius: 6,
                barThickness: 32
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { color: '#e2e8f0' } },
                x: { grid: { color: '#e2e8f0' } }
            },
            plugins: {
                legend: { display: false },
                tooltip: { callbacks: { label: (ctx) => ` ${ctx.raw} новостей` } }
            }
        }
    });
}

async function loadAllStats() {
    const endpoints = {
        text: 'http://127.0.0.1:8001/get_text_stat',
        pie: 'http://127.0.0.1:8001/get_round_agency_stat',
        bar: 'http://127.0.0.1:8001/get_news_per_day_stat'
    };

    try {
        const [textRes, pieRes, barRes] = await Promise.all([
            fetch(endpoints.text), fetch(endpoints.pie), fetch(endpoints.bar)
        ]);

        const [textData, pieData, barData] = await Promise.all([
            textRes.json(), pieRes.json(), barRes.json()
        ]);

        updateTextStats(textData);
        renderPieChart(pieData);
        renderBarChart(barData);

    } catch (e) {
        showToast('Ошибка сервера', duration=2000, type="red");
    }
}

// Кнопка "Обновить"
async function refreshStats() {
    const btn = document.querySelector('.refresh-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Обновление...';
    }
    await loadAllStats();
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> <span>Обновить</span>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadAllStats();
})

loadAllStats();

const refreshBtn = document.querySelector('.refresh-btn');
if (refreshBtn) {
    refreshBtn.addEventListener('click', refreshStats);
}