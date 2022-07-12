import requests
import json

def scrape_activity(url):
    page = requests.get(url)
    start_index = page.text.find('recentActivity&quot;:[') + len('recentActivity&quot;:[')

    if start_index <= 0:
        raise Exception

    current_index = start_index
    starters = 1
    closers = 0
    while starters != closers:
        if page.text[current_index] == '[':
            starters += 1
        elif page.text[current_index] == ']':
            closers += 1
        current_index += 1
    
    return json.loads('[' + page.text[start_index:current_index-1].replace('&quot', '"').replace('\\/', '/').replace(';', '') + ']')

def scrape_avatar_url(url):
    page = requests.get(url)

    start_index = page.text.rfind('avatar_url&quot;:&quot;') + len('avatar_url&quot;:&quot;')
    if start_index <= 0:
        raise Exception
    end_index = page.text.find('&quot', start_index) + len('&quot')    
    
    return page.text[start_index:end_index-len('&quot')].replace('&quot', '"').replace('\\/', '/').replace(';', '')
    
