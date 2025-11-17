
REDDIT_POST_TEMPLATES = [
# --- Template 1 ---
"""
👨‍💻 <b>{{ title | safe }}</b>
{% if image_url %}
<a href="{{ image_url }}">&#8205;</a>
{% endif %}

{% if extract_snippet %}
{{ extract_snippet | safe }}
{% elif selftext %}
{{ selftext[:4000] | safe }}...
{% endif %}

<b>Author:</b> {{ author }}
  
<b>Subreddit:</b> r/{{ subreddit }}
  
👍 {{ score  }} upvotes | 💬 {{ num_comments  }} comments  

<a href="{{ permalink }}">Read on Reddit</a>
{% if steam_appid %}
<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam Page</a>
{% endif %}

#indiegames #gamedev #{{ subreddit }}
""",

# --- Template 2 ---
"""
🎮 <b>{{ title | safe }}</b>  
{% if image_url %}

<a href="{{ image_url }}">&#8205;</a>
{% endif %}

> {% if extract_snippet %}{{ extract_snippet | safe }}{% elif selftext %}{{ selftext[:4000] | safe }}...{% endif %}

🧩 Shared by {{ author  }} on r/{{ subreddit }}
  
<a href="{{ permalink }}">Open Reddit Thread</a>  

👍 {{ ups }} upvotes | 💬 {{ num_comments }} comments

{% if steam_appid %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam Page</a>
{% endif %}

#indiedev #community #{{ subreddit }}
""",

# --- Template 3 ---
"""
💬 <b>{{ title | safe }}</b>
{% if image_url %}

<a href="{{ image_url }}">&#8205;</a>
{% endif %}

{% if extract_snippet %}
{{ extract_snippet | safe }}

{% elif selftext %}
{{ selftext[:4000] | safe }}...

{% endif %}

🔗 <a href="{{ permalink }}">Discuss on Reddit</a>  

👍 {{ ups }} upvotes | 💬 {{ num_comments }} comments
  
{% if steam_appid %}
<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam Page</a>

{% endif %}
#indiegames #reddit #{{ subreddit }}
"""
]
