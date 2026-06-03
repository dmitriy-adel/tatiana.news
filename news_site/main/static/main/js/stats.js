// Глобальные переменные графиков
let pieChartInstance = null;
let barChartInstance = null;

const chartColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'];

// === ДЕМОНСТРАЦИОННЫЕ ДАННЫЕ (если бэкенд недоступен) ===
const sampleTextData = {
    total_news: "1248",
    total_sources: "47",
    total_users: "312",
    most_popular_source: "РИА Новости"
};

const samplePieData = {
    "Сборщик РИА": 32,
    "Сборщик ТАСС": 27,
    "Сборщик Интерфакс": 18,
    "Сборщик Lenta": 14,
    "Другие агенты": 9
};

const sampleBarData = {
    "Пн": 92, "Вт": 118, "Ср": 87, "Чт": 134, "Пт": 76, "Сб": 41, "Вс": 59
};

// === БЛОК 2: Текстовая статистика ===
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

// === БЛОК 4: Круговая диаграмма ===
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

// === БЛОК 3: Гистограмма (7 столбцов) ===
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

// === Загрузка данных с API ===
async function loadAllStats(useSample = false) {
    const endpoints = {
        text: 'http://127.0.0.1:8000/get_text_stat',
        pie: 'http://127.0.0.1:8000/get_round_agents_stat',
        bar: 'http://127.0.0.1:8000/get_round_news_per_day_stat'
    };

    try {
        if (useSample) {
            updateTextStats(sampleTextData);
            renderPieChart(samplePieData);
            renderBarChart(sampleBarData);
            return;
        }

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
        console.warn('Бэкенд недоступен — используются демонстрационные данные');
        updateTextStats(sampleTextData);
        renderPieChart(samplePieData);
        renderBarChart(sampleBarData);
    }
}

// Кнопка "Обновить"
async function refreshStats() {
    const btn = document.querySelector('.refresh-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Обновление...';
    }
    await loadAllStats(false);
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> <span>Обновить</span>';
    }
}

// Запуск при загрузке
document.addEventListener('DOMContentLoaded', () => {
    loadAllStats(false); // сначала пытается реальный API, потом fallback
})
