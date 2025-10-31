GAME_POST_TEMPLATES = [
    # --- Template 1 ---
    """
<b>{{ name }}</b> — a fresh indie release on Steam 🎮

{{ short_description }}

<b>Developed by:</b> {{ developers }}
<b>Publishers:</b> {{ publishers }}
<b>Genres:</b> {{ genres }}
<b>Platforms:</b> {{ platforms }}
<b>Languages:</b> {{ supported_languages }}
<b>Release date:</b> {{ release_date }}

{% if image_url %}
<a href="https://store.steampowered.com/app/{{ steam_appid }}"><img src="{{ image_url }}"></a>
{% endif %}

<a href="{{ website }}">Official Website</a> |
<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam Page</a>

#{{ tags }}
""",

    # --- Template 2 ---
    """
🔥 <b>{{ name }}</b> is out now on Steam!

{{ short_description }}

<b>Publishers:</b> {{ publishers }}
<b>Developers:</b> {{ developers }}
<b>Genres:</b> {{ genres }}
<b>Release date:</b> {{ release_date }}

{% if image_url %}
<a href="https://store.steampowered.com/app/{{ steam_appid }}"><img src="{{ image_url }}"></a>
{% endif %}

<a href="{{ website }}">Website</a> |
<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>

#{{ tags }}
""",

    # --- Template 3 ---
    """
🎨 <b>{{ name }}</b> — a beautiful new indie game with {{ genres }} vibes

{{ short_description }}

<b>Available on:</b> {{ platforms }}
<b>Developed by:</b> {{ developers }}
<b>Tags:</b> {{ tags }}

{% if image_url %}
<a href="https://store.steampowered.com/app/{{ steam_appid }}"><img src="{{ image_url }}"></a>
{% endif %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">🕹️ View on Steam</a>
"""
]
