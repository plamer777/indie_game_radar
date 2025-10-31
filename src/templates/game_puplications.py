GAME_POST_TEMPLATES = [
    # --- Template 1 ---
    """
<b>{{ name }}</b> — a fresh indie release on Steam 🎮
<br>
{{ short_description }}
<br>
<b>Developed by:</b> {{ developers }}
<br>
<b>Publishers:</b> {{ publishers }}
<br>
<b>Genres:</b> {{ genres }}
<br>
<b>Platforms:</b> {{ platforms }}
<br>
<b>Languages:</b> {{ supported_languages }}
<br>
<b>Release date:</b> {{ release_date }}
<br>

{% if image_url %}
<a href="https://store.steampowered.com/app/{{ steam_appid }}"><img src="{{ image_url }}"></a>
{% endif %}
<br>
<a href="{{ website }}">Official Website</a> |
<br>
<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam Page</a>
<br>
{% if tags %}
#{{ tags }}
{% endif %}
""",

    # --- Template 2 ---
    """
🔥 <b>{{ name }}</b> is out now on Steam!
<br>
{{ short_description }}
<br>
<b>Publishers:</b> {{ publishers }}
<br>
<b>Developers:</b> {{ developers }}
<br>
<b>Genres:</b> {{ genres }}
<br>
<b>Release date:</b> {{ release_date }}
<br>

{% if image_url %}
<a href="https://store.steampowered.com/app/{{ steam_appid }}"><img src="{{ image_url }}"></a>
{% endif %}
<br>
<a href="{{ website }}">Website</a>
<br>
<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>
<br>
{% if tags %}
#{{ tags }}
{% endif %}
""",

    # --- Template 3 ---
    """
🎨 <b>{{ name }}</b> — a beautiful new indie game with {{ genres }} vibes
<br>
{{ short_description }}
<br>
<b>Available on:</b> {{ platforms }}
<br>
<b>Developed by:</b> {{ developers }}
<br>
{% if tags %}
<b>Tags:</b> {{ tags }}
{% endif %}
<br>
{% if image_url %}
<a href="https://store.steampowered.com/app/{{ steam_appid }}"><img src="{{ image_url }}"></a>
{% endif %}
<br>
<a href="https://store.steampowered.com/app/{{ steam_appid }}">🕹️ View on Steam</a>
"""
]
