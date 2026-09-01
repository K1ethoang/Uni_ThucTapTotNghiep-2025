# Uni_ThucTapTotNghiep-2025

> Ứng dụng **Change Data Capture (CDC)** để chuyển đổi / đồng bộ dữ liệu thời gian thực giữa các hệ quản trị cơ sở dữ liệu: **MySQL → MongoDB**.

Báo cáo thực tập tốt nghiệp *"Ứng dụng Change Data Capture (CDC) để chuyển đổi dữ liệu giữa các hệ quản trị cơ sở dữ liệu"* – Trường ĐH Giao thông Vận tải (Phân hiệu TP.HCM), thực tập tại FPT Telecom, 2025.

📄 Xem chi tiết [báo cáo](https://github.com/K1ethoang/My-Achievements/blob/main/Reports/4th-year/TTTN.pdf)

![Sơ đồ CDC](assets/cdc.png)

---

## Cách hoạt động

1. **Bắt thay đổi ở MySQL** – **Debezium** (chạy trên Kafka Connect) kết nối MySQL qua `binlog` (`binlog-format=ROW`), ghi lại mọi `INSERT / UPDATE / DELETE` ở cấp dòng.
2. **Đẩy sự kiện vào Kafka** – mỗi bảng MySQL tương ứng một topic `mysql.<database>.<table>`. Cụm Kafka gồm **2 broker** (`9092`, `9093`), mỗi topic 2 partition.
3. **Tiêu thụ & ghi vào MongoDB** – `consumer-worker.py` (Kafka consumer, chạy ngoài Django nhưng dùng `settings` của Django) subscribe pattern `^mysql\.employees\..*`, giải mã payload Debezium và áp dụng thay đổi vào MongoDB:
   - `op = c` / `r` → `insert_one`
   - `op = u` → `update_one` (`$set`, match theo bản ghi `before`)
   - `op = d` → `delete_one` (match theo `before`)
   - Trường ngày (`from_date`, `to_date`) được chuyển từ số ngày epoch sang `datetime`.
4. **Ứng dụng mẫu Django** – cung cấp Django Admin + ORM models (map tới các bảng của bộ dữ liệu mẫu `employees`, `managed = False`).

## Bộ dữ liệu

Sử dụng **Employees Sample Database** của MySQL: <https://github.com/datacharmer/test_db> (đã kèm trong thư mục `test_db/`).
Các bảng: `employees`, `departments`, `dept_emp`, `dept_manager`, `titles`, `salaries`.

## Yêu cầu

- Python **3.13**
- Docker & Docker Compose
- MySQL client (để nạp dữ liệu mẫu)

## Cài đặt & chạy

### 1. Chuẩn bị

```bash
# tạo file .env từ mẫu
cp dev.env .env
```

Điền `.env`:

```env
DEBUG=True

DB_MYSQL_DATABASE=employees
DB_MYSQL_USER=root
DB_MYSQL_PASSWORD=your_password
DB_MYSQL_HOST=127.0.0.1
DB_MYSQL_PORT=3306

DB_MONGODB_DATABASE=cdc
DB_MONGODB_HOST=127.0.0.1
DB_MONGODB_USER=
DB_MONGODB_PASS=
DB_MONGODB_PORT=27017

CONSUMER_GROUP_ID=cdc-group
KAFKA_TOTAL_THREAD=3
KAFKA_TOTAL_WORKER=1     # = số partition của topic
```

### 2. Khởi động hạ tầng (Docker)

```bash
docker compose --env-file .env -f ./docker/docker-compose.yml up -d --build
```

Các service: `mysql` (bật binlog ROW), `mongodb`, `zookeeper`, `kafka-1`, `kafka-2`, `kafka-connect` (Debezium 2.7.3), `kafka-ui`.

### 3. Nạp dữ liệu mẫu vào MySQL

```bash
# trong thư mục test_db (hoặc dùng script test_db/load-data.sh trong container mysql)
mysql -h 127.0.0.1 -u root -p employees < test_db/employees.sql
```

### 4. Đăng ký Debezium connector

```bash
docker exec -it kafka-connect bash
# kiểm tra Kafka Connect đã sẵn sàng
curl -s http://localhost:8083/
# đăng ký connector cho MySQL
sh /register-connector.sh
```

### 5. Chạy ứng dụng Django + consumer

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser --username admin

python manage.py runserver                          # terminal 1 – Django admin
python applications/employee/consumer-worker.py      # terminal 2 – CDC consumer (MySQL -> MongoDB)
```

### 6. Truy cập

| URL | Mô tả |
|---|---|
| <http://127.0.0.1:8000/admin> | Django Admin – thao tác CRUD trên các bảng MySQL |
| <http://127.0.0.1:5000> | Kafka UI – theo dõi broker / topic / consumer / message |

Thử nghiệm: thêm / sửa / xoá bản ghi trong Django Admin (hoặc trực tiếp trong MySQL) → quan sát message trong Kafka UI → dữ liệu tương ứng được cập nhật trong MongoDB (`cdc` database, collection trùng tên bảng).

## Cấu trúc thư mục

```
Uni_ThucTapTotNghiep-2025/
├── manage.py
├── requirements.txt
├── dev.env                         # mẫu biến môi trường (đổi tên -> .env)
├── cdc_project/                    # cấu hình Django (settings, MySQL + Mongo + Kafka)
├── applications/employee/
│   ├── models.py                   # ORM map bảng employees (managed = False)
│   ├── admin.py                    # Django Admin
│   ├── mongodb.py                  # MongoDb.replicate_data() – áp dụng CDC event
│   └── consumer-worker.py          # Kafka consumer đa tiến trình / đa luồng
├── docker/
│   ├── docker-compose.yml          # MySQL, MongoDB, Zookeeper, 2 Kafka broker, Kafka Connect, Kafka UI
│   ├── register-mysql.json         # cấu hình Debezium MySQL connector
│   └── register-connector.sh
└── test_db/                        # Employees Sample Database (datacharmer/test_db)
```

## Hạn chế & hướng phát triển

- Topic chỉ 2 partition, một consumer group → giới hạn throughput khi tải cao.
- Chưa có cơ chế retry / error handling khi ghi MongoDB thất bại.
- Hướng mở rộng: tăng partition, thêm consumer, tích hợp Apache Flink / Spark Streaming.
