from rich.console import Console
from rich.table import Table
import requests
import xml.etree.ElementTree as ET
import csv
import json
import re
import os

console = Console()

print("""
__     _______ ____ _____ ____ _____ 
\ \   / / ____/ ___| ____|  _ \_   _|
 \ \ / /|  _|| |   |  _| | |_) || |  
  \ V / | |__| |___| |___|  _ < | |  
   \_/  |_____\____|_____|_| \_\|_|  

         VECERT - Security Research Tool
 For Educational Use Only | Cybercrime Investigation
""")

PROTON_HEADERS = {
    "accept": "application/vnd.protonmail.v1+json",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "x-pm-appversion": "web-account@5.0.270.1",
    "x-pm-locale": "en_US",
    "x-pm-ov": "lax",
    "x-pm-uid": "upyulffn33faq6mnwkuzz7q2qjqekalz",
    "origin": "https://account.proton.me",
    "referer": "https://account.proton.me/signup",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "pragma": "no-cache",
    "cache-control": "no-cache"
}

PROTON_COOKIES = {
    "AUTH-upyulffn33faq6mnwkuzz7q2qjqekalz": "y6iuhnkaogtvhzjrfa4jf7xo2mykln6e",
    "Session-Id": "aIYuoSom-KqULYafC086vAAAAQ8"
}

EXTENDED_DOMAINS = [
    "protonmail.com", "protonmail.ch", "tutanota.com", "tuta.io", "tutanota.de",
    "outlook.com", "outlook.es", "hotmail.com", "hotmail.co.uk", "yahoo.com",
    "yandex.com", "riseup.net", "mailfence.com", "pm.me", "cock.li", "safe-mail.net",
    "guerrillamail.com", "disroot.org", "secmail.pro", "proton.me"
]

def print_table(headers, rows):
    table = Table(show_header=True, header_style="bold magenta")
    for header in headers:
        table.add_column(header, style="cyan")
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    console.print(table)

def check_proton(username):
    results = []
    for domain in ["proton.me", "protonmail.com", "protonmail.ch", "pm.me"]:
        email = f"{username}@{domain}"
        params = {"Name": email, "ParseDomain": "1"}
        try:
            r = requests.get("https://account.proton.me/api/core/v4/users/available",
                             headers=PROTON_HEADERS, cookies=PROTON_COOKIES, params=params, timeout=10)
            data = r.json()
            status = " Email exists" if data.get("Error") == "Username already taken" else " Email not exists"
            suggestions = data.get("Details", {}).get("Suggestions", [])
            results.append([email, status, ", ".join(suggestions) if suggestions else "-"])
        except Exception as e:
            results.append([email, f"⚠️ Error: {e}", "-"])
    return results

def verify_api_x(email):
    url = f"https://api.x.com/i/users/email_available.json?email={email}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return "Account not exists" if data.get("valid") and not data.get("taken") else "❌ Account exists"
        else:
            return f"⚠️ HTTP {r.status_code}"
    except Exception as e:
        return f"⚠️ Error: {e}"

def check_email_x(username):
    results = []
    for domain in EXTENDED_DOMAINS:
        email = f"{username}@{domain}"
        status = verify_api_x(email)
        results.append([email, status])
    return results

def show_profile_links(username, uid):
    links = [
        ["Profile URL", f"https://darkforums.st/User-{username}"],
        ["Avatar Image", f"https://darkforums.st/uploads/avatars/avatar_{uid}.jpg"],
        ["User Posts", f"https://darkforums.st/search.php?action=finduser&uid={uid}"],
        ["User Threads", f"https://darkforums.st/search.php?action=finduserthreads&uid={uid}"],
        ["Reputation Page", f"https://darkforums.st/reputation.php?uid={uid}"],
        ["Telegram Profile", f"https://t.me/{username}"],
        ["OSINT - WhatsMyName", f"https://whatsmyname.app/?q={username}"],
        ["OSINT - IDCrawl", f"https://www.idcrawl.com/u/{username}"],
        ["OSINT - Social Searcher", f"https://www.social-searcher.com/google-social-search/?q={username}"],
        ["BreachForums Search", f"https://bf.based.re/search/{username}"],
        ["Check Telegram History", "https://t.me/unamer_news"]
    ]
    print_table(["Type", "URL"], links)

def search_user():
    username = input("🔍 Enter username to search on DarkForums: ").strip()
    url = f"https://darkforums.st//xmlhttp.php?action=get_users&query={username}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        usuarios = r.json()
        if not usuarios:
            console.print("❌ No users found on DarkForums.")
            return
        rows = [[str(i+1), user['id'], user['uid']] for i, user in enumerate(usuarios)]
        print_table(["#", "Username", "UID"], rows)
        seleccion = input("➡️ Select ID from table to see full profile and OSINT: ").strip()
        if not seleccion.isdigit():
            console.print("❌ Invalid input.")
            return
        seleccion = int(seleccion)
        if 1 <= seleccion <= len(usuarios):
            user = usuarios[seleccion - 1]
            username = user['id']
            uid = user['uid']
            show_profile_links(username, uid)
            console.print("\n📧 ProtonMail Check:")
            print_table(["Email", "ProtonMail Status", "Suggestions"], check_proton(username))
            console.print("\n📡 External Email Availability Check:")
            print_table(["Email", "Status"], check_email_x(username))
        else:
            console.print("❌ Invalid selection.")
    except Exception as e:
        console.print(f"⚠️ Error fetching DarkForums data: {e}")

def show_breaches():
    try:
        r = requests.get("https://darkforums.st/syndication.php", timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        rows = []
        for item in items[:10]:
            title = item.find("title").text.strip()
            link = item.find("link").text.strip()
            author_tag = item.find("{http://purl.org/dc/elements/1.1/}creator")
            author = re.search(r'>(.*?)<', author_tag.text).group(1) if author_tag is not None else "Unknown"
            rows.append([title[:60] + '...' if len(title) > 60 else title, author, link])
        print_table(["Title", "Author", "Link"], rows)
    except Exception as e:
        console.print(f"⚠️ Error fetching RSS: {e}")

def search_breach_csv():
    query = input("🔍 Enter Title or Author to search in CSVs: ").strip().lower()
    files = ["leaks_output.csv", "sellers_output.csv"]
    results = []
    for file in files:
        if not os.path.exists(file): continue
        with open(file, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if query in row['Title'].lower() or query in row['Author'].lower():
                    results.append([row['Title'], row['Author'], row['Thread_URL']])
    if results:
        print_table(["Title", "Author", "Thread URL"], results)
    else:
        console.print("❌ No results found in CSV files.")

def search_user_backup():
    if not os.path.exists("darkforums_users.json"):
        console.print("❌ darkforums_users.json file not found.")
        return

    with open("darkforums_users.json", encoding='utf-8') as f:
        all_users = json.load(f)

    keyword = input("🔍 Enter partial username to search in backup: ").strip().lower()
    filtered_users = [u for u in all_users if keyword in u['user'].lower()]

    if not filtered_users:
        console.print(f"❌ No users found containing: '{keyword}'")
        return

    rows = [[str(i+1), user['user'], user['URL']] for i, user in enumerate(filtered_users)]
    print_table(["#", "Username", "Profile URL"], rows)

    seleccion = input("➡️ Select ID from table to consult OSINT and email info: ").strip()
    if not seleccion.isdigit():
        console.print("❌ Please enter a valid number.")
        return
    seleccion = int(seleccion)

    if 1 <= seleccion <= len(filtered_users):
        username = filtered_users[seleccion - 1]['user']
        console.print("\n📧 ProtonMail Check:")
        print_table(["Email", "ProtonMail Status", "Suggestions"], check_proton(username))
        console.print("\n📡 External Email Availability Check:")
        print_table(["Email", "Status"], check_email_x(username))
        show_profile_links(username, "backup")
    else:
        console.print("❌ Invalid selection.")


def menu():
    while True:
        console.print("\n[bold blue]=== Intelligence Menu ===[/bold blue]")
        console.print("[green]1.[/green] 🔍 Search User + Profile + ProtonMail Check + OSINT + Email Availability")
        console.print("[green]2.[/green] 📢 View Latest Breaches ")
        console.print("[green]3.[/green] 🔍 Search Breach ")
        console.print("[green]4.[/green] 🔍 Search User Backup ")
        console.print("[red]5.[/red] ❌ Exit")
        choice = input("Select an option: ").strip()
        if choice == "1": search_user()
        elif choice == "2": show_breaches()
        elif choice == "3": search_breach_csv()
        elif choice == "4": search_user_backup()
        elif choice == "5": break
        else: console.print("[red]❌ Invalid option.[/red]")

if __name__ == "__main__":
    menu()
