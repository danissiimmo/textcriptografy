import ctypes 
import sys
import os
import hashlib
import mysql.connector
from tkinter import *
from tkinter import messagebox
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

# Проверка прав администратора
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(sys.argv), None, 1)
    sys.exit()

def check_flash_key():
    flash_drive_path = 'E:\\'  # путь к флешке
    secret_file = os.path.join(flash_drive_path, 'flash_key.txt')

    if os.path.exists(secret_file):
        with open(secret_file, 'r') as file:
            flash_key = file.read().strip()
            return flash_key
    else:
        return None  # Возвращаем None, если файл не найден

def verify_flash_key(flash_key):
    # Настроить соединение с базой данных
    conn = mysql.connector.connect(
        host="192.168.192.119",
        user="root",
        password="",
        database="messenger_db",
        port=3307
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `keys` WHERE flash_key_hash=%s", (hashlib.sha256(flash_key.encode()).hexdigest(),))
    result = cursor.fetchone()
    conn.close()
    return bool(result)

# GUI Приложение
class MessengerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Защищённый Мессенджер")
        self.root.geometry("400x600")
        self.root.configure(bg="#222831")

        self.login_screen()

    # Экран разблокировки
    def login_screen(self):
        self.clear_screen()
        Label(self.root, text="Вставьте флешку для разблокировки", font=("Arial", 14), fg="#eeeeee", bg="#222831").pack(pady=30)
        Button(self.root, text="Разблокировать", command=self.unlock, bg="#00adb5", fg="#eeeeee", font=("Arial", 12)).pack(pady=10)

    # Функция разблокировки
    def unlock(self):
        flash_key = check_flash_key()
        if flash_key:
            if verify_flash_key(flash_key):
                self.user_login_screen()  # Переходим к экрану ввода логина и пароля
            else:
                messagebox.showerror("Ошибка", "Неверный ключ!")
        else:
            messagebox.showerror("Ошибка", "Носитель не распознан!")

    # Экран логина
    def user_login_screen(self):
        self.clear_screen()
        Label(self.root, text="Введите имя пользователя и пароль", font=("Arial", 14), fg="#eeeeee", bg="#222831").pack(pady=30)

        Label(self.root, text="Логин", font=("Arial", 12), fg="#eeeeee", bg="#222831").pack(pady=5)
        self.username_entry = Entry(self.root, font=("Arial", 12))
        self.username_entry.pack(pady=5)

        Label(self.root, text="Пароль", font=("Arial", 12), fg="#eeeeee", bg="#222831").pack(pady=5)
        self.password_entry = Entry(self.root, font=("Arial", 12), show="*")
        self.password_entry.pack(pady=5)

        self.error_label = Label(self.root, text="", font=("Arial", 10), fg="red", bg="#222831")
        self.error_label.pack()

        Button(self.root, text="Войти", command=self.verify_login, bg="#00adb5", fg="#eeeeee", font=("Arial", 12)).pack(pady=10)

    # Верификация входа
    def verify_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        user_data = self.get_user_credentials(username, password)
        if user_data:
            self.username = username
            self.unique_key = user_data['unique_key']
            self.user_id = user_data['id']  # Устанавливаем user_id из полученных данных
            self.chat_screen()  # Переходим в окно чата
        else:
            self.error_label.config(text="Ошибка: Неверное имя пользователя или пароль")

    # Получение данных пользователя из базы данных
    def get_user_credentials(self, username, password):
        conn = mysql.connector.connect(
            host="192.168.192.119",
            user="root",
            password="",
            database="messenger_db",
            port=3307
        )
        cursor = conn.cursor(dictionary=True)
        username_hash = hashlib.sha256(username.encode()).hexdigest()
        cursor.execute("SELECT id, unique_key FROM `users` WHERE login=%s AND password=%s", 
                    (username_hash, hashlib.sha256(password.encode()).hexdigest()))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            self.unique_key = user_data['unique_key']  # Сохраняем уникальный ключ пользователя
        return user_data

    # Экран чата
    def chat_screen(self):
        self.clear_screen()
        self.messages_frame = Frame(self.root)
        self.messages_frame.pack(expand=True, fill=BOTH)

        self.messages_listbox = Listbox(self.messages_frame, bg="#393e46", fg="#eeeeee", font=("Arial", 12), selectbackground="#00adb5")
        self.messages_listbox.pack(expand=True, fill=BOTH, padx=10, pady=10)

        self.message_entry = Entry(self.root, font=("Arial", 12))
        self.message_entry.pack(pady=5, padx=10, fill=X)

        Button(self.root, text="Отправить", command=self.send_message, bg="#00adb5", fg="#eeeeee", font=("Arial", 12)).pack(pady=10)

        self.load_messages()



    # Метод для шифрования сообщения
    def encrypt_message(self, message):
        if not self.unique_key:
            print("Ошибка: уникальный ключ не загружен")  # Проверка наличия ключа перед шифрованием
            return ""
        print("Ключ для шифрования:", self.unique_key)  # Вывод ключа шифрования в консоль
        fernet = Fernet(self.unique_key.encode())  # Используем уникальный ключ
        encrypted_message = fernet.encrypt(message.encode())
        return encrypted_message.decode()  # Возвращаем зашифрованное сообщение как строку

    # Метод для расшифрования сообщения
    # Метод для расшифрования сообщения с использованием ключа отправителя
    def decrypt_message(self, encrypted_message, unique_key):
        try:
            fernet = Fernet(unique_key.encode())  # Используем переданный уникальный ключ
            decrypted_message = fernet.decrypt(encrypted_message.encode())
            return decrypted_message.decode()  # Возвращаем расшифрованное сообщение как строку
        except InvalidToken:
            return "[Ошибка расшифровки]"  # Возвращаем строку с ошибкой, если ключ неверный

    # Метод для загрузки сообщений из базы данных
    def load_messages(self):
        conn = mysql.connector.connect(
            host="192.168.192.119",
            user="root",
            password="",
            database="messenger_db",
            port=3307
        )
        cursor = conn.cursor(dictionary=True)
        # Объединяем таблицы messages и users для извлечения логина и уникального ключа отправителя
        cursor.execute("""
            SELECT messages.message, messages.timestamp, users.login, users.unique_key 
            FROM messages 
            JOIN users ON messages.sender_id = users.id
            ORDER BY messages.timestamp ASC
        """)
        messages = cursor.fetchall()
        conn.close()

        for message in messages:
            decrypted_message = self.decrypt_message(message['message'], message['unique_key'])
            # Форматируем строку с логином, расшифрованным сообщением и временной меткой
            self.messages_listbox.insert(
                END, 
                f"{message['login']} ({message['timestamp']}): {decrypted_message}"
            )
            
    # Отправка сообщения
    def send_message(self):
        message = self.message_entry.get()
        if message:
            encrypted_message = self.encrypt_message(message)
            # Сохранение зашифрованного сообщения в базе данных
            self.save_message_to_db(encrypted_message)
            self.message_entry.delete(0, END)
            self.update_messages()  # Обновляем сообщения в интерфейсе

    # Метод для обновления сообщений
    def update_messages(self):
        self.messages_listbox.delete(0, END)  # Очищаем текущее отображение сообщений
        self.load_messages()  # Загружаем новые сообщения из базы данных

    # Отображение сообщений
    def display_message(self, sender_name, encrypted_message):
        # Дешифруем сообщение перед его показом
        decrypted_message = self.decrypt_message(encrypted_message)
        self.chat_box.insert(END, f"{sender_name}: {decrypted_message}\n")
    
    # Метод для сохранения сообщения в базе данных
    def save_message_to_db(self, encrypted_message):
        conn = mysql.connector.connect(
            host="192.168.192.119",
            user="root",
            password="",
            database="messenger_db",
            port=3307
        )
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (sender_id, message) VALUES (%s, %s)", (self.user_id, encrypted_message))
        conn.commit()
        cursor.close()
        conn.close()

    # Очистка экрана
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

# Запуск приложения
if __name__ == "__main__":
    root = Tk()
    app = MessengerApp(root)
    root.mainloop()
