# 📅 Hướng dẫn cập nhật dữ liệu hàng ngày

## 🚀 Cách sử dụng

### Cập nhật dữ liệu (mỗi ngày 1 lần)

```bash
cd c:\Users\duylu\OneDrive\Desktop\Additional_Data\steel-flow-analysis
python update_daily.py
```

**Thời gian:** Khoảng 2-3 phút

---

## 📊 Script sẽ làm gì?

1. **Fetch dữ liệu mới** từ CaféF và Smoney:
   - Khối ngoại (Foreign trading)
   - Tự doanh (Self trading)
   - Định giá PE/PB (Valuation)
   - VN-Index

2. **Export ra Excel files**:
   - `steel_foreign_trading.xlsx`
   - `steel_self_trading.xlsx`
   - `steel_valuation.xlsx`
   - `vnindex_market.xlsx`

3. **Git operations**:
   - Add files
   - Commit với message: `"Update data: 2025-12-15"`
   - Push lên GitHub `origin/main`

4. **Streamlit Cloud** tự động redeploy (3-5 phút)

---

## ✅ Output mẫu

```
============================================================
     Steel Flow Analysis - Daily Data Update
============================================================

[09:00:00] Project root: C:\Users\duylu\...\steel-flow-analysis

[09:00:00] Starting data fetch and export...

[09:00:00] Running export_excel.py...

============================================================
STEEL TRADING & VALUATION DATA EXPORT
============================================================
Tickers: HPG, HSG, NKG, TLH, VIS, SMC, POM, TVN
...

[09:02:15] Data fetch and export completed successfully!

[09:02:15] Checking Excel files...
[09:02:15] ✓ steel_foreign_trading.xlsx (557.2 KB)
[09:02:15] ✓ steel_self_trading.xlsx (87.4 KB)
[09:02:15] ✓ steel_valuation.xlsx (394.1 KB)
[09:02:15] ✓ vnindex_market.xlsx (54.3 KB)

[09:02:16] Starting git operations...
[09:02:16] Adding files to git...
[09:02:16] ✓ Files staged
[09:02:16] Committing: Update data: 2025-12-15
[09:02:17] ✓ Committed: abc1234
[09:02:17] Pushing to origin/main...
[09:02:20] ✓ Pushed to origin/main

============================================================
     Update completed successfully!
============================================================
Duration: 2m 20s

Next steps:
1. GitHub received the commit
2. Streamlit Cloud will detect changes (~1-2 min)
3. App will redeploy automatically (~1-2 min)
4. Users will see fresh data within ~5 minutes
```

---

## ⚠️ Xử lý lỗi

### Nếu API lỗi (CaféF/Smoney down)
- Script vẫn tiếp tục
- Commit dữ liệu có được
- In cảnh báo ra terminal

### Nếu Git lỗi (conflicts, network)
- Script dừng lại
- In lỗi chi tiết
- Exit code 1

### Nếu không có thay đổi
- Script báo "No changes to commit"
- Không tạo commit mới
- Exit thành công

---

## 🔧 Troubleshooting

### Lỗi: "export_excel.py not found"
```bash
# Kiểm tra file có tồn tại
ls Stock-analyst/export_excel.py
```

### Lỗi: "Git operation failed"
```bash
# Kiểm tra git status
git status

# Pull changes nếu có conflict
git pull origin main
```

### Lỗi: "Module not found"
```bash
# Cài đặt dependencies
pip install -r requirements.txt
```

---

## 📝 Lưu ý

1. **Kết nối internet**: Cần internet để fetch data và push lên GitHub
2. **Chạy 1 lần/ngày**: Đủ để cập nhật dữ liệu mới nhất
3. **Thời điểm chạy**: Nên chạy sau 18h (sau giờ đóng cửa thị trường)
4. **Git conflicts**: Không xảy ra vì chỉ bạn update data

---

## 🚀 Tự động hóa (Optional)

### Windows Task Scheduler
1. Mở Task Scheduler
2. Create Basic Task
3. Trigger: Daily 18:30
4. Action: Start a program
   - Program: `python`
   - Arguments: `update_daily.py`
   - Start in: `C:\Users\duylu\...\steel-flow-analysis`

### Cron (Linux/Mac)
```bash
# Chạy mỗi ngày lúc 18:30
30 18 * * * cd /path/to/steel-flow-analysis && python update_daily.py
```

---

## 📞 Support

Nếu có vấn đề, kiểm tra:
1. Terminal output có lỗi gì không
2. Excel files có được tạo/update không
3. GitHub có commit mới không
4. Streamlit Cloud có redeploy không
