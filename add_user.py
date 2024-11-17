import tkinter as tk
from tkinter import messagebox
import mysql.connector
import hashlib
import random
import string
from cryptography.fernet import Fernet

# Функция для генерации случайного пароля
def generate_password():
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    password = ''.join(random.choice(characters) for i in range(12))
    password_entry.delete(0, tk.END)  # Очищаем поле пароля
    password_entry.insert(0, password)  # Вставляем сгенерированный пароль

# Функция для генерации уникального ключа (подходит для Fernet)
def generate_unique_key():
    unique_key = Fernet.generate_key()  # Генерируем 32-байтовый Base64 ключ
    return unique_key.decode()  # Возвращаем ключ в формате строки для сохранения в БД

# Функция для добавления пользователя в базу данных
def add_user_to_db():
    login = name_entry.get().strip()
    password = password_entry.get().strip()
    
    if not login or not password:
        messagebox.showwarning("Ошибка", "Введите имя и пароль!")
        return
    
    # Хэшируем имя пользователя и пароль
    login_hash = hashlib.sha256(login.encode()).hexdigest()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    unique_key = generate_unique_key()
    
    try:
        # Подключаемся к базе данных
        conn = mysql.connector.connect(
            host="192.168.192.119",
            user="root",
            password="",
            database="messenger_db",
            port=3307
        )
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь с таким именем
        cursor.execute("SELECT id FROM users WHERE login=%s", (login_hash,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует. Попробуйте другое имя.")
            return
        
        # Добавляем пользователя с уникальным ключом
        cursor.execute("INSERT INTO users (login, password, unique_key) VALUES (%s, %s, %s)", (login_hash, password_hash, unique_key))
        conn.commit()
        
        messagebox.showinfo("Успех", "Пользователь успешно добавлен.")
        
        # Очищаем поля после добавления
        name_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
        
    except mysql.connector.Error as err:
        messagebox.showerror("Ошибка", f"Ошибка добавления пользователя: {err}")
    
    finally:
        cursor.close()
        conn.close()

# Функция для показа/скрытия пароля
def toggle_password():
    if password_entry.cget('show') == '*':
        password_entry.config(show='')
        toggle_password_btn.config(text="Скрыть пароль")
    else:
        password_entry.config(show='*')
        toggle_password_btn.config(text="Показать пароль")

# Создаем GUI
root = tk.Tk()
root.title("Добавление пользователя")
root.geometry("400x350")

# Метка и поле ввода для имени
tk.Label(root, text="Имя пользователя:").pack(pady=5)
name_entry = tk.Entry(root, width=30)
name_entry.pack(pady=5)

# Метка и поле ввода для пароля
tk.Label(root, text="Пароль:").pack(pady=5)
password_entry = tk.Entry(root, width=30, show="*")
password_entry.pack(pady=5)

# Кнопка "Показать пароль"
toggle_password_btn = tk.Button(root, text="Показать пароль", command=toggle_password)
toggle_password_btn.pack(pady=5)

# Кнопка для генерации пароля
generate_btn = tk.Button(root, text="Сгенерировать пароль", command=generate_password)
generate_btn.pack(pady=10)

# Кнопка для добавления пользователя
add_user_btn = tk.Button(root, text="Добавить пользователя", command=add_user_to_db)
add_user_btn.pack(pady=10)

root.mainloop()
