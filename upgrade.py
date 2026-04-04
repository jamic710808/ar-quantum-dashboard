import re

with open('AR_Dashboard_V3_0_Ultimate.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('V3.0 - Ultimate 旗艦版', 'V4.0 - Ultimate 旗艦版')
html = html.replace('V3.0 ULTIMATE', 'V4.0 ULTIMATE')
html = html.replace('AR_Template_V3_0.xlsx', 'AR_Template_V4_0.xlsx')
html = html.replace('<h1>應收帳款戰略指揮中心</h1>', '<h1 style="display:flex;align-items:center"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:12px; filter: drop-shadow(0 0 8px rgba(255,215,0,0.5))"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg> 應收帳款戰略指揮中心</h1>')

chart_js_script = '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n</head>'
html = html.replace('</head>', chart_js_script)

svgs = {
    '期末應收餘額': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px; filter: drop-shadow(0 0 4px var(--cyan))"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>',
    '累計營收': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px; filter: drop-shadow(0 0 4px var(--success))"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>',
    '應收帳款比率': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px; filter: drop-shadow(0 0 4px var(--warning))"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>',
    '應收帳款周轉率': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--purple)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px; filter: drop-shadow(0 0 4px var(--purple))"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>',
    '滾動 DSO（12個月）': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
    '加權平均帳齡': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',
    '信用資金成本': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px"><rect x="2" y="5" width="20" height="14" rx="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line></svg>',
    '信用評分分佈': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 6.91 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>',
}

for title, svg in svgs.items():
    html = html.replace(f'<div class="card-lbl">{title}', f'<div class="card-lbl" style="display:flex;align-items:center">{svg}{title}')

radar_html = '''
            <!-- Radar Chart Added for V4.0 -->
            <div class="card" style="margin-bottom:16px">
                <div class="card-lbl" style="display:flex;align-items:center"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"></polygon></svg>綜合客戶信用雷達圖<span>COMPREHENSIVE CREDIT SCORING RADAR</span></div>
                <div class="chart-wrap" style="height:320px; display:flex; justify-content:center;">
                    <canvas id="chart-radar" style="max-height:100%;"></canvas>
                </div>
            </div>
'''
html = html.replace('<div class="tab-content" id="tab2">\n            <div class="grid-2"', f'<div class="tab-content" id="tab2">\n{radar_html}            <div class="grid-2"')

radar_js = '''
        let radarChartInstance = null;
        function drawRadar() {
            const canvas = document.getElementById('chart-radar');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            
            const clients = getFiltered();
            if(!clients.length) return;
            
            const totalBal = clients.reduce((s, c) => s + c.bal, 0);
            const avgBal = totalBal / clients.length;
            const avgAging = clients.reduce((s, c) => s + c.aging, 0) / clients.length;
            const avgLoss = clients.reduce((s, c) => s + c.loss, 0) / clients.length;
            const safeCount = clients.filter(c => c.risk === 'safe' || c.risk === 'low').length;
            const highRiskCount = clients.filter(c => c.risk === 'high' || c.risk === 'critical').length;
            
            // Normalize scores (0-100) for display, higher is better
            const maxBal = 15; 
            const scoreSize = Math.max(0, 100 - (avgBal/maxBal)*100);
            
            const maxAgingVal = 60;
            const scoreEfficiency = Math.max(0, 100 - (avgAging/maxAgingVal)*100);
            
            const maxLoss = 300;
            const scoreCost = Math.max(0, 100 - (avgLoss/maxLoss)*100);
            
            const scoreSafety = (safeCount / clients.length) * 100;
            const scoreRiskControl = Math.max(0, 100 - ((highRiskCount / clients.length) * 100 * 2)); // Penalty for high risk
            
            const data = {
                labels: ['資金規模健康度', '帳齡回收效率', '壞帳控制能力', '優質客戶佔比', '高危風險控制'],
                datasets: [{
                    label: '當前群體綜合評分',
                    data: [scoreSize.toFixed(1), scoreEfficiency.toFixed(1), scoreCost.toFixed(1), scoreSafety.toFixed(1), scoreRiskControl.toFixed(1)],
                    fill: true,
                    backgroundColor: 'rgba(0, 212, 255, 0.15)',
                    borderColor: 'rgba(0, 212, 255, 0.8)',
                    pointBackgroundColor: 'rgba(255, 215, 0, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(255, 215, 0, 1)'
                }]
            };
            
            if (radarChartInstance) {
                radarChartInstance.data = data;
                radarChartInstance.update();
            } else {
                radarChartInstance = new Chart(ctx, {
                    type: 'radar',
                    data: data,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        color: 'rgba(240, 240, 248, 0.7)',
                        scales: {
                            r: {
                                min: 0,
                                max: 100,
                                angleLines: { color: 'rgba(255, 255, 255, 0.15)' },
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                pointLabels: { color: 'rgba(240, 240, 248, 0.9)', font: { size: 11, family: 'Inter' } },
                                ticks: { display: false }
                            }
                        },
                        plugins: {
                            legend: {
                                labels: { color: 'rgba(240, 240, 248, 0.9)', font: { family: 'Inter' } }
                            }
                        }
                    }
                });
            }
        }
'''
html = html.replace('function drawAll() {', radar_js + '\n        function drawAll() {')
html = html.replace('drawBubble();', 'drawBubble(); drawRadar();')

with open('AR_Dashboard_V4_0_Ultimate.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('V4 HTML Generated!')
