import tkinter as tk
from tkinter import ttk, messagebox, LabelFrame
import requests
import os
import pygame
import spotipy
import time
from PIL import Image, ImageTk
from spotipy.oauth2 import SpotifyOAuth
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import threading, sys

class SpotifyMusicPlayerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Spotify Music Player Preview")
        self.CLIENT_ID = '81f31ee0b429453b8f60b5faf4e9479c'
        self.CLIENT_SECRET = '265086020308417ab64aebda485eb148'
        self.REDIRECT_URI = 'http://localhost:8888/callback'
        self.config_file = 'spotify_credentials.ini'
        self.sp = self.authenticate_spotify()
        self.track_uri = None
        self.track_name = tk.StringVar()
        self.artist_name = tk.StringVar()
        self.album_name = tk.StringVar()
        self.album_image = tk.PhotoImage()
        self.selected_track_id = None
        pygame.mixer.init()
        self.playback_thread = None  # To store the playback thread
          # Flag to track if login information has been submitted
        self.create_ui()
    def authenticate_spotify(self):
        config = SpotifyOAuth(
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            redirect_uri=self.REDIRECT_URI,
            scope='user-library-read user-read-playback-state user-modify-playback-state'
        )

        return spotipy.Spotify(auth_manager=config)

    def create_ui(self):
        self.group_box1 = LabelFrame(self.master, text="Thông Tin", padx=10, pady=10)
        self.track_label = tk.Label(self.group_box1, textvariable=self.track_name, font=('Helvetica', 8, 'bold'))
        self.artist_label = tk.Label(self.group_box1, textvariable=self.artist_name, font=('Helvetica', 8))
        self.album_label = tk.Label(self.group_box1, textvariable=self.album_name, font=('Helvetica', 8))
        self.album_image_label = tk.Label(self.group_box1, image=self.album_image)

        self.group_box2 = LabelFrame(self.master, text="Tài Khoản", padx=10, pady=10)
        self.username_label = ttk.Label(self.group_box2, text="Username:")
        self.password_label = ttk.Label(self.group_box2, text="Password:")
        self.username_entry = ttk.Entry(self.group_box2, width=30)
        self.password_entry = ttk.Entry(self.group_box2, width=30, show='*')

        self.search_label = ttk.Label(self.master, text="Tên Bài Hát:")
        self.search_entry = ttk.Entry(self.master, width=30)
        self.search_button = ttk.Button(self.master, text="Tìm Kiếm", command=self.search_and_play_track)
        self.search_results_listbox = tk.Listbox(self.master, width=50, height=10)
        self.search_results_listbox.grid(row=4, column=0, columnspan=3, pady=10, padx=10, sticky='w')
        self.search_results_listbox.bind("<ButtonRelease-1>", self.on_listbox_click)
       
        self.group_box1.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky='ew')
        self.track_label.grid(row=0, column=0, columnspan=2, pady=10)
        self.artist_label.grid(row=1, column=0, columnspan=2, pady=5)
        self.album_label.grid(row=2, column=0, columnspan=2, pady=5)
        self.album_image_label.grid(row=0, column=2, rowspan=3, padx=10)

        self.search_label.grid(row=3, column=0, padx=10, pady=5, sticky='e')
        self.search_entry.grid(row=3, column=1, padx=5, pady=10, sticky='w')
        self.search_button.grid(row=3, column=2, padx=5, pady=10, sticky='w')

        self.group_box2.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky='ew')
        self.username_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.username_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.password_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.password_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        self.transfer_button = ttk.Button(self.master, text="Phát Nhạc", command=self.open_browser_and_transfer_info)
        self.transfer_button.grid(row=7, column=0, columnspan=3, pady=10)
    def load_album_image(self, url):
        response = requests.get(url)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img = img.resize((150, 150))
        self.album_image = ImageTk.PhotoImage(img)
        self.album_image_label.config(image=self.album_image)
    def search_and_play_track(self):
        self.search_results_listbox.delete(0, tk.END)
        track_name = self.search_entry.get()
        if track_name:
            results = self.sp.search(q=track_name, type='track', limit=10)
            for idx, track_info in enumerate(results['tracks']['items']):
                self.search_results_listbox.insert(tk.END, f"{idx + 1}. {track_info['name']} - {track_info['artists'][0]['name']}")
            return track_name
        return None
    def on_listbox_click(self, event):
        selected_index = self.search_results_listbox.curselection()
        if selected_index:
            selected_index = int(selected_index[0])
            results = self.sp.search(q=self.search_entry.get(), type='track', limit=10)
            track_info = results['tracks']['items'][selected_index]
            self.track_name.set(track_info['name'])
            self.artist_name.set("Nghệ sĩ: " + track_info['artists'][0]['name'])
            self.album_name.set("Album: " + track_info['album']['name'])
            image_url = track_info['album']['images'][0]['url']
            self.load_album_image(image_url)
            self.selected_track_id = track_info['id']  # Remove this line

    def open_browser_and_transfer_info(self):
        try:
            username = self.username_entry.get()
            password = self.password_entry.get()

            thread = threading.Thread(target=self.transfer_info_in_webdriver, args=(username, password))
            thread.start()

        except Exception as e:
            messagebox.showerror("Lỗi Đăng nhập", f"Đăng nhập thất bại: {str(e)}")

    def transfer_info_in_webdriver(self, username, password):
        try:
            driver = webdriver.Chrome()
            # chrome_options = Options()
            # chrome_options.add_argument("--headless")
            # chrome_options.add_argument("--window-size=420,626")
            # driver = webdriver.Chrome(options=chrome_options)
            # driver.set_window_size(500,400)
            driver.get('https://accounts.spotify.com/en/login')
            # driver.set_window_size(200, 200)
            username_field = driver.find_element(By.ID, 'login-username')
            password_field = driver.find_element(By.ID, 'login-password')
            login_button = driver.find_element(By.XPATH, '//*[@id="login-button"]/span[1]/span')
            username_field.send_keys(username)
            password_field.send_keys(password)
            login_button.click()
            time.sleep(5)
            initial_track_id = None  # Store the initial track ID

            while True:
                if self.selected_track_id and driver:
                    # Check if the track ID has changed
                    if self.selected_track_id != initial_track_id:
                        driver.get(f"https://open.spotify.com/track/{self.selected_track_id}")
                        time.sleep(2)
                        button_element = driver.find_element(By.XPATH,'/html/body/div[4]/div/div[2]/div[3]/div[1]/div[2]/div[2]/div/div/div[2]/main/section/div[3]/div[4]/div/div/div/div/div/button/span')
                        button_element.click()
                        initial_track_id = self.selected_track_id  # Update the initial track ID

                    # Your existing code for controlling playback

                else:
                    messagebox.showinfo("Thông báo", "Vui lòng chọn một bài hát trước khi chuyển thông tin.")
                    break  # Break the loop if no track is selected

        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {str(e)}")

        finally:
            if driver:
                driver.quit()

    def start_playback(self, track_id):
        self.sp.start_playback(uris=[f"spotify:track:{track_id}"])

    def select_track(self, track_id):
        self.selected_track_id = track_id
if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifyMusicPlayerApp(root)
    root.mainloop()