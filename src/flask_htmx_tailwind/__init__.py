import re
import jinja_partials
from urllib.parse import urlparse, urlunparse
import feedparser
import html
from flask import Flask, abort, jsonify, render_template, request

verge_rss_url = 'https://www.theverge.com/rss/index.xml'
josh_w_comeau_rss_url = 'https://www.joshwcomeau.com/rss.xml'

feeds = { 
    verge_rss_url: {
        'title': 'The Verge Blog',
        'href': verge_rss_url,
        'show_images': True,
        'entries': {}
    },
    josh_w_comeau_rss_url: {
        'title': 'Josh W. Comeau',
        'href': josh_w_comeau_rss_url,
        'show_images': True,
        'entries': {}
    }
}


def extract_main_image(entry):
    for content in entry.get('content', []):
        if content.get('type') == 'text/html':
            html = content.get('value', '')
            match = re.search(r'<img[^>]+src="([^"]+)"', html)
            if match:
                return match.group(1)
    return None

def create_app():
    app = Flask(
        __name__,
        template_folder='./templates',
        static_folder='../static'
    )
    jinja_partials.register_extensions(app)

    @app.route('/')
    @app.route('/feed/<path:feed_url>')
    def render_feed(feed_url: str | None = None):
        for url, feed_ in feeds.items():
            parsed_feed = feedparser.parse(url)
            for entry in parsed_feed.entries:
                if entry['link'] not in feed_['entries']:
                    if url == verge_rss_url:
                        entry['media_content'] = [extract_main_image(entry)]
                    feed_['entries'][entry['link']] = entry

        feed = list(feeds.values())[0]
        if feed_url != None:
            feed = feeds[feed_url]
        return render_template(
            'feed.html', 
            feed=feed, 
            entries=feed['entries'].values(),
            feeds=feeds
        )
    
    @app.route('/entries/<path:feed_url>')
    def render_feed_entries(feed_url: str):
        try:
            feed = feeds[feed_url]
        except KeyError:
            abort(400)
    
        page = int(request.args.get('page', 0))

        return render_template(
            'partials/entry_page.html',
            entries=list(feed['entries'].values())[page*5:page*5+5],
            href=feed_url,
            page=page,
            max_page=len(feed['entries'])//5
        )

    return app