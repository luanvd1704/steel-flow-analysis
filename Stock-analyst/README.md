# 📊 Ứng dụng Phân tích Dòng tiền CaféF

Ứng dụng Streamlit để phân tích dòng tiền Khối ngoại và Tự doanh cho cổ phiếu Việt Nam từ dữ liệu CaféF.

## 🚀 Cài đặt

```bash
pip install -r requirements.txt
```

## ▶️ Chạy ứng dụng

```bash
streamlit run app.py
```

Hoặc với UTF-8 encoding (Windows):

```bash
python -X utf8 -m streamlit run app.py
```

## 📋 Tính năng

### 1. 📈 Dòng tiền ròng theo thời gian
- Biểu đồ line chart với fill màu
- Xanh: Mua ròng, Đỏ: Bán ròng
- Hiển thị xu hướng dòng tiền theo thời gian

### 2. 📊 Mua vs Bán
- Bar chart so sánh giá trị mua và bán
- Tùy chỉnh số ngày hiển thị
- Dữ liệu khối ngoại và tự doanh

### 3. 🔗 Giá + Dòng tiền
- Combo chart kết hợp dòng tiền và giá cổ phiếu
- Hiển thị mối liên hệ giữa 2 yếu tố
- Lưu ý: Hiện sử dụng giá mô phỏng

## ⚙️ Tùy chỉnh

- **Mã cổ phiếu**: Nhập mã bất kỳ (HPG, VNM, VIC, etc.)
- **Khoảng thời gian**: 1 tháng, 3 tháng, 6 tháng, 1 năm, 2 năm, Tất cả
- **Số ngày Bar Chart**: Slider 10-120 ngày
- **Cache**: Dữ liệu được cache 1 giờ, có thể làm mới thủ công

## 📁 Cấu trúc file

```
Stock-analyst/
├── app.py                          # Ứng dụng Streamlit chính
├── fetch_cafef_trade_data.py       # Module fetch dữ liệu CaféF
├── requirements.txt                # Dependencies
└── README.md                       # File này
```

## 💡 Lưu ý

- Dữ liệu được fetch trực tiếp từ CaféF API
- Cache tự động 1 giờ để giảm tải server
- Không lưu file vật lý, tất cả trong memory
- Giá cổ phiếu hiện tại là mô phỏng, cần kết nối API giá thật

## 🔧 Troubleshooting

### Lỗi encoding trên Windows
```bash
python -X utf8 -m streamlit run app.py
```

### Lỗi timeout
- Kiểm tra kết nối mạng
- Thử lại sau vài phút
- CaféF API có thể giới hạn request

### Cài đặt thêm thư viện
```bash
pip install streamlit pandas plotly requests
```
