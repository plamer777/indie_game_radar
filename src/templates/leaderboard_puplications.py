GAME_LEADERBOARD_TEMPLATES = [

# ============================
# 1) Dynamic Short Leaderboard Post
# ============================
"""
🏆 <b>{{ game_name | safe }}</b>

Here are the current leaders across main categories:

{% for cl in category_leaderboards %}
<b>{{ loop.index }}. {{ cl.category.name }}</b>
• <b>{{ cl.result.player.name }}</b> — place: <b>{{ cl.result.place }}</b>
{% if cl.result.times %}
• Time: {{ cl.result.times.realtime_t }} seconds
{% endif %}
{% if cl.result.videos %}
• Video: <a href="{{ cl.result.videos[0] }}">watch</a>
{% endif %}
{% if cl.result.comment %}
• Comment: {{ cl.result.comment }}
{% endif %}
{% endfor %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>
""",


# ============================
# 2) Analytical Leaderboard Overview
# ============================
"""
🎮 <b>{{ game_name | safe }}</b>

<b>📊 Current category records:</b>

{% for cl in category_leaderboards %}
<b>{{ cl.category.name }}</b>
• Player: <a href="{{ cl.result.player.weblink }}">{{ cl.result.player.name }}</a>  
• Place: <b>{{ cl.result.place }}</b>  
{% if cl.result.times %}
• Result: {{ cl.result.times.realtime_t }} seconds  
{% endif %}
{% if cl.result.date %}
• Run date: {{ cl.result.date.strftime("%Y-%m-%d") }}  
{% endif %}
{% if cl.result.videos %}
• Video: <a href="{{ cl.result.videos[0] }}">watch</a>  
{% endif %}
—
{% endfor %}

🔗 <a href="{{ weblink }}">Leaderboard</a> | <a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>
""",


# ============================
# 3) Editorial Leaderboard Breakdown
# ============================
"""
📝 <b>{{ game_name | safe }}</b>

<b>Leaderboard highlights:</b>

{% for cl in category_leaderboards %}
<b>🏅 {{ cl.category.name }}</b>  
Player: <b>{{ cl.result.player.name }}</b>  
Place: <code>{{ cl.result.place }}</code>  

{% if cl.result.times %}
⏱ Time: <code>{{ cl.result.times.get('realtime_t', '') }} seconds</code>  
{% endif %}

{% if cl.result.comment %}
💬 Comment: “{{ cl.result.comment }}”  
{% endif %}

{% if cl.result.videos %}
🎥 Video: <a href="{{ cl.result.videos[0] }}">watch</a>  
{% endif %}

📌 <a href="{{ cl.weblink }}">Category details</a>
{% if not loop.last %}
<hr>
{% endif %}
{% endfor %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>
"""
]
