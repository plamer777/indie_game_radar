
REDDIT_POST_TEMPLATES = [
    # --- Template 1 ---
    """
👨‍💻 <b>{{ title }}</b>
<br>
{% if image_url %}
<img src="{{ image_url }}">
<br>
{% endif %}
{% if extract_snippet %}
{{ extract_snippet }}
<br>
{% elif selftext %}
{{ selftext[:1000] }}...
<br>
{% endif %}

<b>Author:</b> {{ author }}
<br>  
<b>Subreddit:</b> r/{{ subreddit }}
<br>  
👍 {{ score  }} upvotes | 💬 {{ num_comments  }} comments  
<br>
<a href="{{ permalink }}">Read on Reddit</a>
<br>
#indiegames #gamedev {{ subreddit }}
""",

    # --- Template 2 ---
    """
🎮 <b>{{ title }}</b>  
<br>
{% if image_url %}
<img src="{{ image_url }}">
<br>
{% endif %}
> {% if extract_snippet %}{{ extract_snippet }}{% elif selftext %}{{ selftext[:1000] }}...{% endif %}
<br>
🧩 Shared by {{ author  }} on r/{{ subreddit }}
<br>  
<a href="{{ permalink }}">Open Reddit Thread</a>
<br>  
#indiedev #community {{ subreddit }}
""",

    # --- Template 3 ---
    """
💬 <b>{{ title }}</b>
<br>
{% if image_url %}
<img src="{{ image_url }}">
<br>
{% endif %}
{% if extract_snippet %}
{{ extract_snippet }}
<br>
{% elif selftext %}
{{ selftext[:1000] }}...
<br>
{% endif %}

🔗 <a href="{{ permalink }}">Discuss on Reddit</a>  
<br>
👍 {{ ups }} upvotes | 💬 {{ num_comments }} comments
<br>  
#indiegames #reddit {{ subreddit }}
"""
]
