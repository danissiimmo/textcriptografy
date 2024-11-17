import os
import hashlib
import mysql.connector

def add_flash_key_from_file(key_file_path):
    # Проверяем, существует ли файл с ключом
    if not os.path.exists(key_file_path):
        print(f"Файл {key_file_path} не найден!")
        return

    # Считываем ключ из файла
    with open(key_file_path, 'r') as file:
        flash_key = file.read().strip()

    # Хешируем ключ
    hashed_key = hashlib.sha256(flash_key.encode()).hexdigest()

    # Настроить соединение с базой данных
    conn = mysql.connector.connect(
        host="192.168.192.119",
        user="root",
        password="",
        database="messenger_db",
        port=3307
    )
    cursor = conn.cursor()

    # Добавляем хеш в базу данных, заменяя его, если id = 1 уже существует
    cursor.execute("""
        INSERT INTO `keys` (id, flash_key_hash)
        VALUES (1, %s)
        ON DUPLICATE KEY UPDATE flash_key_hash = %s
    """, (hashed_key, hashed_key))
    
    conn.commit()

    # Записываем только хеш обратно в файл
    with open(key_file_path, 'w') as file:
        file.write(hashed_key)

    # Перемещаем оригинальный ключ в flash_key_nohash.txt
    nohash_file_path = 'E:\\flash_key_nohash.txt'
    with open(nohash_file_path, 'w') as file:
        file.write(flash_key)

    print("Ключ успешно добавлен и обработан.")

    cursor.close()
    conn.close()

# Пример использования
add_flash_key_from_file('E:\\flash_key.txt')  # Укажите путь к файлу с ключом
