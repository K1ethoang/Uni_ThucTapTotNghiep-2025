#!/bin/bash
set -e  # Dừng nếu có lỗi
echo "Waiting for MySQL to start..."
until mysql -h mysql -u root -p"${DB_MYSQL_PASSWORD}" -e "SELECT 1;" &> /dev/null; do
  echo "MySQL is not ready yet. Waiting..."
  sleep 10
done
echo "MySQL is ready!"
echo "Go to test_db folder"
cd /test_db
echo "Running database initialization..."
mysql -h mysql -u root -p"${DB_MYSQL_PASSWORD}" "${DB_MYSQL_DATABASE}" < employees.sql
echo "Database initialization completed!"
