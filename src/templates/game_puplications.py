GAME_POST_TEMPLATES = [
# --- Template 1 ---
"""
<b>{{ name }}</b> — a fresh indie release on Steam 🎮
{% if image_url %}
<a href="{{ image_url }}">&#8205;</a>
{% endif %}

{{ short_description | safe }}

<b>Developed by:</b> {{ developers }}

<b>Publishers:</b> {{ publishers }}

<b>Genres:</b> {{ genres }}

<b>Platforms:</b> {{ platforms }}

<b>Languages:</b> {{ supported_languages }}

<b>Release date:</b> {{ release_date }}

<b>Recommendations:</b> {{ recommendations }}

<b>Price:</b> {{ price }}

<a href="{{ website }}">Official Website</a>

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam Page</a>

{% if tags %}
#{{ tags }}
{% endif %}
""",

# --- Template 2 ---
"""
🔥 <b>{{ name }}</b> is out now on Steam!
{% if image_url %}
<a href="{{ image_url }}">&#8205;</a>
{% endif %}

{{ short_description | safe }}

<b>Publishers:</b> {{ publishers }}

<b>Developers:</b> {{ developers }}

<b>Genres:</b> {{ genres }}

<b>Release date:</b> {{ release_date }}

<b>Recommendations:</b> {{ recommendations }}

<b>Price:</b> {{ price }}

<a href="{{ website }}">Website</a>

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>
{% if tags %}
#{{ tags }}
{% endif %}
""",

# --- Template 3 ---
"""
🎨 <b>{{ name }}</b> — a beautiful new indie game with {{ genres }} vibes
{% if image_url %}
<a href="{{ image_url }}">&#8205;</a>
{% endif %}

{{ short_description | safe }}

<b>Available on:</b> {{ platforms }}

<b>Developed by:</b> {{ developers }}
{% if tags %}
<b>Tags:</b> {{ tags }}
{% endif %}

<b>Genres:</b> {{ genres }}

<b>Release date:</b> {{ release_date }}

<b>Recommendations:</b> {{ recommendations }}

<b>Price:</b> {{ price }}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">🕹️ View on Steam</a>
"""
]
