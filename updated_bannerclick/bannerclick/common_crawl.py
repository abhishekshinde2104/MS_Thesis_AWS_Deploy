import requests
import json

url = 'https://index.commoncrawl.org/CC-MAIN-2022-16-index?url=google.com&output=json'

response = requests.get(url)

if response.status_code == 200:
    for line in response.content.decode('utf-8').splitlines():
        record = json.loads(line)
        if 'mime' in record and record['mime'] == 'text/html':
            html_url = record['url']
            html_content = requests.get(html_url).content.decode('utf-8')
            print(html_content)
else:
    print('Error getting response')