import datetime
import jsonpickle
import requests
import bs4
import re

from urllib.parse import urlsplit

class prop:
    def __init__(self, id, url, title, price, sqm):
        self.id = id
        self.url = url
        self.title = title
        self.price = price
        self.sqm = sqm
    
    def __str__(self):
        return "id %s, %s EUR, %s m2" % (self.id, self.price, self.sqm)

class scraperrun:
    def __init__(self, start_url):
        self.start_url = start_url
        self.ts_start = None
        self.ts_end = None

        self.props = {
            '123' : prop('1', '', '', '', ''),
            '234' : prop('2', '', '', '', '')}
        
    def __str__(self):
        return f'url: {self.start_url} started: {self.ts_start} props: {len(self.props)}'
    
    def start_run(self, max_results = 2000):
        self.ts_start = datetime.datetime.now()

        i = 0
        res = None

        next_url = sr.start_url
        split_url = urlsplit(sr.start_url)
        base_url = f'{split_url.scheme}://{split_url.netloc}'
        
        while i < max_results:

            if res is None:
                res = requests.get(next_url)
                if res.status_code != 200:
                    print(f'Cannot get {next_url}')
                    exit(1)

                urls = re.findall('\"\/iad\/immobilien\/d\/.*?\/\"', res.text) 
                
                for u in urls:
                    url = base_url + u[1:-1]
                    try:
                        prop = scraperrun.crawl_page(url)
                        self.props[prop.id] = prop
                        print(prop)
                    except:
                        print(f'Cannot parse {u}')

                    i += 1
                    if i >= max_results:
                        break

                tmp = scraperrun.get_next_page(res)
                if tmp is None:
                    break
                
                next_url = base_url + tmp
                res = None
            
        print(f'{i} properties crawled')
    
    def end_run(self):
        self.ts_end = datetime.datetime.now()

    # crawl one page and return property object
    def crawl_page(url):
        res = requests.get(url)
        html = bs4.BeautifulSoup(res.text, 'html.parser')

        title = html.title.contents[0]
        id = re.findall('-\d+\/$', url)[0][1:-1]
        price = sqm = 0
        
        soup = html.find_all(text=re.compile('Gesamtmiete inkl. MWSt'))
        if len(soup) > 0:
            str = re.findall('\d+[\.|,]?\d*[\.|,]?\d*', soup[0].parent.parent.text)[0]
            price = scraperrun.string_to_int(str)

        soup = html.find_all(text=re.compile('Wohnfläche'))
        if len(soup) > 0:
                str = re.findall('\d*[,\d*]', soup[0].parent.parent.next_sibling.text)
                if str is not None:
                    sqm = scraperrun.string_to_int(str[0])
        else:
            soup = html.find_all(text=re.compile('Nutzfläche'))
            if len(soup) > 0:
                str = re.findall('\d*[,\d*]', soup[0].parent.parent.next_sibling.text)[0]
                sqm = scraperrun.string_to_int(str)
            
        # return valid object or None if bogus
        if sqm > 0 and price > 0 and len(title) > 0 and len(id) > 0:
            return prop(id, url, title, price, sqm)
        else:
            return None

    # get url of next page of search results
    def get_next_page(res):
        html = bs4.BeautifulSoup(res.text, 'html.parser')

        """ # get total number or search results -> optional
        total_results = html.find_all('h1', {'data-testid': 'result-list-title'})
        total = re.findall('\d*', total_results[0].text.replace('.', ''))[0]
        print(f'Total number of listings: {total}')
        """       
        # return the URL of the 'next' page
        try:
            soup = html.find_all('a', {'data-testid': 'pagination-top-next-button'})
            for s in soup:
                return s['href']
        except:
            return None

    # convert string containing EUR currency to int (hack, to be improved)
    def string_to_int(str):
        result = 0
        if ',' in str:
            str = str[0:str.rfind(',')] # ignore beyond first ','
        if '.' in str:
            str = str.replace('.', '') # remove all '.'s
        result = int(str)
        return result

if __name__ == "__main__":
    
    sr = scraperrun('https://www.willhaben.at/iad/immobilien/mietwohnungen/oberoesterreich/linz?page=1&rows=100')
    sr.start_run(5)
    sr.end_run()
    exit(1)

    sr = scraperrun('willhaben.at')
    sr.start_run()
    sr.props['345'] = prop('3', '', '', '', '')

    print(sr)
    for s in sr.props:
        print(sr.props[s])
    
    sr.end_rund()
    
    str = jsonpickle.encode(sr)
    print(str)
    print('---')

    new_sr = jsonpickle.decode(str)
    print(new_sr)
    new_key = '999666333'
    if new_key in new_sr.props:
        print('-> already exists')
    else:
        print(f'-> adding {new_key}')
        new_sr.props[new_key] = prop('4', '4', '4', '4', '4')

    for s in new_sr.props:
        print(new_sr.props[s])
    
    runs = []
    runs.append(sr)
    runs.append(new_sr)
