import pandas as pd

# 1. 客戶資料
data_clients = {
    '客戶名稱': ['【必填】字串', '國巨電腦(股)', '緯創資通', '和碩聯合', '聯電', '日月光半導體', '群創光電', '長榮海運', '陽明海運', '萬海航運', '聯發科技', '台積電', '三星電子-TV', '美光科技', '高通科技'],
    '所屬城市 (taipei/hsinchu/taichung/kaohsiung)': ['【必填】代碼', 'taipei', 'taipei', 'taipei', 'hsinchu', 'kaohsiung', 'hsinchu', 'taipei', 'taipei', 'taipei', 'hsinchu', 'hsinchu', 'taichung', 'taichung', 'hsinchu'],
    '應收餘額(M)': ['【必填】數字', 15.5, 8.2, 5.4, 12.1, 7.8, 4.3, 18.5, 9.6, 6.2, 22.4, 45.8, 3.2, 11.5, 8.9],
    '加權帳齡(天)': ['【必填】數字', 42, 25, 18, 55, 38, 12, 65, 48, 22, 15, 8, 95, 33, 19],
    '信用資金成本率': ['【必填】小數', 0.018, 0.005, 0.002, 0.025, 0.012, 0.001, 0.035, 0.022, 0.006, 0.0005, 0.0002, 0.058, 0.009, 0.003],
    '風險等級 (safe/low/mid/high/critical)': ['【必填】代碼', 'high', 'low', 'safe', 'critical', 'mid', 'safe', 'critical', 'critical', 'mid', 'safe', 'safe', 'critical', 'mid', 'safe'],
    '預計壞帳損失(K)': ['【必填】數字', 450, 80, 0, 600, 230, 0, 1100, 480, 120, 0, 0, 640, 310, 0],
    '建議策略': ['【必填】字串', '立即清收', '維持現狀', '提升授信', '現款結算', '加強催收', '提升授信', '現款結算', '現款結算', '加強催收', '提升授信', '提升授信', '法務介入', '加強催收', '提升授信']
}
df_clients = pd.DataFrame(data_clients)

# 2. 月趨勢
data_months = {
    '月份': ['【必填】YYYY-MM', '2025-09', '2025-10', '2025-11', '2025-12', '2026-01', '2026-02'],
    '期末應收餘額(M)': ['【必填】數字', 125.4, 130.2, 128.5, 142.6, 155.8, 179.4],
    '滾動DSO(天)': ['【必填】數字', 48.2, 49.5, 47.8, 52.1, 55.3, 58.7]
}
df_months = pd.DataFrame(data_months)

# 3. 帳齡結構
data_stack = {
    '月份': ['【必填】YYYY-MM', '2025-09', '2025-10', '2025-11', '2025-12', '2026-01', '2026-02'],
    '未逾期(%)': ['【必填】數字', 55, 54, 56, 52, 48, 45],
    '1-30天(%)': ['【必填】數字', 20, 21, 19, 22, 23, 22],
    '31-90天(%)': ['【必填】數字', 15, 14, 15, 16, 18, 19],
    '91-365天(%)': ['【必填】數字', 8, 9, 8, 8, 9, 11],
    '365天以上(%)': ['【必填】數字', 2, 2, 2, 2, 2, 3]
}
df_stack = pd.DataFrame(data_stack)

# 4. 帳齡明細
data_buckets = {
    '帳齡區間': ['【必填】字串', '未逾期 / CURRENT', '1-30天 / 1-30 DAYS', '31-90天 / 31-90 DAYS', '91-365天 / 91-365 DAYS', '365天以上 / OVER 1 YEAR'],
    '金額(M)': ['【必填】數字', 80.7, 39.5, 34.1, 19.7, 5.4],
    '佔比(%)': ['【必填】數字', 45, 22, 19, 11, 3],
    '壞帳準備率(%)': ['【必填】數字', 0, 1, 3, 5, 20],
    '預計損失(K)': ['【必填】數字', 0, 395, 1023, 985, 1080]
}
df_buckets = pd.DataFrame(data_buckets)

# 5. 總覽參數
data_params = {
    '參數名稱': ['【請勿修改名稱】', '累計營收 (M)', '年化利率', '目標 DSO（天）', '目標 AR 比率', '壞帳預備率', '行業平均 DSO', '資料截止月份'],
    '數值': ['【請修改此列】', 1250.5, 0.055, 45.0, 0.14, 0.025, 52.5, '2026-02']
}
df_params = pd.DataFrame(data_params)

# 輸出 Excel
with pd.ExcelWriter('AR_Template_V4_0.xlsx', engine='openpyxl') as writer:
    df_clients.to_excel(writer, sheet_name='客戶資料', index=False)
    df_months.to_excel(writer, sheet_name='月趨勢', index=False)
    df_stack.to_excel(writer, sheet_name='帳齡結構', index=False)
    df_buckets.to_excel(writer, sheet_name='帳齡明細', index=False)
    df_params.to_excel(writer, sheet_name='總覽參數', index=False)

print('V4 Excel Data Template Generated!')
