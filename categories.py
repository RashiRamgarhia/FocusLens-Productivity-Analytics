# categories.py

CATEGORY_NAMES = ["Productive", "Neutral", "Distracting"]

PRODUCTIVE_APPS = [
    "code",
    "pycharm64",
    "idea64",
    "spyder",
    "sublime_text",
    "notepad++",
    "windowsterminal",
    "cmd",
    "powershell",
    "winword",
    "excel",
    "powerpnt",
    "postman",
    "obsidian",
    "anaconda-navigator",
    "git-bash"
]

DISTRACTING_APPS = [
    "steam",
    "discord",
    "telegram",
    "whatsapp",
    "snapchat",
    "epicgameslauncher",
    "spotify"
]

PRODUCTIVE_SITES = [
    "github",
    "stack overflow",
    "leetcode",
    "kaggle",
    "geeksforgeeks",
    "colab",
    "jupyter",
    "arxiv",
    "coursera",
    "nptel"
]

DISTRACTING_SITES = [
    "youtube",
    "instagram",
    "facebook",
    "netflix",
    "reddit",
    "twitter",
    "x.com",
    "hotstar",
    "twitch"
]

BROWSERS = ["chrome", "msedge", "firefox", "brave", "opera"]


def get_category(app_name):
    app_lower = str(app_name).lower()
    if app_lower in PRODUCTIVE_APPS or any(s in app_lower for s in PRODUCTIVE_SITES):
        return "Productive"
    if app_lower in DISTRACTING_APPS or any(s in app_lower for s in DISTRACTING_SITES):
        return "Distracting"
    return "Neutral"


def get_app_label(process_name, window_title):
    proc = process_name.lower().replace(".exe", "")
    if proc not in BROWSERS:
        return proc

    title = window_title.lower()
    for site in PRODUCTIVE_SITES + DISTRACTING_SITES:
        if site in title:
            return site
    return proc