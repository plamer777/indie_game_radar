
REDDIT_POST_TEMPLATES = [
    # --- Template 1 ---
    """
👨‍💻 <b>{{ title }}</b>
{% if image_url %}
<img src="{{ image_url }}">
{% endif %}
{% if extract_snippet %}
{{ extract_snippet }}
{% elif selftext %}
{{ selftext[:400] }}...
{% endif %}

<b>Author:</b> {{ author }}  
<b>Subreddit:</b> r/{{ subreddit }}  
👍 {{ score  }} upvotes | 💬 {{ num_comments  }} comments  

<a href="{{ permalink }}">Read on Reddit</a>
#indiegames #gamedev {{ subreddit }}
""",

    # --- Template 2 ---
    """
🎮 <b>{{ title }}</b>  
{% if image_url %}
<img src="{{ image_url }}">
{% endif %}
> {% if extract_snippet %}{{ extract_snippet }}{% elif selftext %}{{ selftext[:250] }}...{% endif %}

🧩 Shared by {{ author  }} on r/{{ subreddit }}  
<a href="{{ permalink }}">Open Reddit Thread</a>  
#indiedev #community {{ subreddit }}
""",

    # --- Template 3 ---
    """
💬 <b>{{ title }}</b>
{% if image_url %}
<img src="{{ image_url }}">
{% endif %}
{% if extract_snippet %}
{{ extract_snippet }}
{% elif selftext %}
{{ selftext[:350] }}...
{% endif %}

🔗 <a href="{{ permalink }}">Discuss on Reddit</a>  
👍 {{ ups or 0 }} upvotes | 💬 {{ num_comments or 0 }} comments  
#indiegames #reddit {{ subreddit or '' }}
"""
]
