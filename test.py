import logging
import argparse
import datetime
import re
import json
import jsonpickle

from urllib.parse import urlsplit
from dataclasses import dataclass
from dataclasses import field


import requests
import bs4
import glob
import Levenshtein

@dataclass(order = True)
class prop:
    id: str
    url: str = field(repr = False)
    title: str = field(repr = False)
    price: float
    sqm: int
    

""" class prop:
    def __init__(self, id, url, title, price, sqm):
        self.id = id
        self.url = url
        self.title = title
        self.price = price
        self.sqm = sqm
    
    def __str__(self):
        return "id: %s, %s EUR, %s m2" % (self.id, self.price, self.sqm)
 """

class scraperrun:
    def __init__(self, start_url, mr = 2000):
        self.start_url = start_url      # willhaben url to start scraping
        self.ts_start = None            # when the scraping run started
        self.ts_end = None              # ... end when it finished
        self.max_results = mr           # guard rail
        self.props = {}                 # store id:prop pairs
        
    def __str__(self):
        return f'url: {self.start_url} started: {self.ts_start} props: {len(self.props)}'
    
    def start_run(self):
        self.ts_start = datetime.datetime.now()

        i = 0
        res = None

        next_url = self.start_url
        
        # get the base url, it's always https://www.willhaben.at ;-)
        split_url = urlsplit(self.start_url)
        base_url = f'{split_url.scheme}://{split_url.netloc}'
        
        while i < self.max_results:

            if res is None:
                # get result page
                res = requests.get(next_url)
                if res.status_code != 200:
                    logging.warning(f'Cannot get {next_url}')
                    exit(1)

                # parse all urls from the Javascript section
                urls = re.findall('\"\/iad\/immobilien\/d\/.*?\/\"', res.text) 
                
                for u in urls:
                    url = base_url + u[1:-1]
                    try:
                        p = scraperrun.crawl_page(url)
                        self.props[p.id] = p
                        logging.info(p)
                    except:
                        logging.warning(f'Cannot parse {u}')

                    i += 1
                    if i >= self.max_results:
                        break

                tmp = scraperrun.get_next_page(res)
                if tmp is None:
                    break
                
                next_url = base_url + tmp
                res = None
            
        logging.info(f'{i} properties crawled')
    
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

    # get url of next page (pagination, click on 'next')
    def get_next_page(res):
        html = bs4.BeautifulSoup(res.text, 'html.parser')

        # get total number or search results -> optional
        #total_results = html.find_all('h1', {'data-testid': 'result-list-title'})
        #total = re.findall('\d*', total_results[0].text.replace('.', ''))[0]
        #print(f'Total number of listings: {total}')

        # return the URL of the 'next' page
        try:
            soup = html.find_all('a', {'data-testid': 'pagination-top-next-button'})
            for s in soup:
                return s['href']
        except:
            return None

    # stats
    def print_stats(self):
        total_price = 0
        total_squarefeet = 0
        
        for p in self.props:
            total_price = total_price + self.props[p].price
            total_squarefeet = total_squarefeet + self.props[p].sqm
        
        no_objects = len(self.props)
        duration = self.ts_end - self.ts_start
        
        print(f'Run started: {self.ts_start}')
        print(f'Pages crawled: {no_objects} [{duration}]')
        print(f'Avg price: {(total_price/no_objects):.2f}')
        print(f'Avg m2: {(total_squarefeet/no_objects):.2f}')
        print(f'Price per m2: EUR {(total_price/total_squarefeet):.2f}')
    
    # write json (FIXME: v1 format)
    def write_json(self, dir = '.'):
        d = self.ts_start
        fname = f'{dir}/run_{d.year}-{d.month}-{d.day}_{d.hour}-{d.minute}-{d.second}.json'
        with open(fname, 'w') as json_file:
            j = jsonpickle.encode(self)
            json_file.write(j)
        
        return fname
        
    # read json (FIXME: v1 format)
    def read_json(fname):
        with open(fname, 'r') as f:
            str = f.read()
            o = jsonpickle.decode(str)
            return o
                
    # convert string containing EUR currency to int (FIXME)
    def string_to_int(str):
        result = 0
        if ',' in str:
            str = str[0:str.rfind(',')] # ignore beyond first ','
        if '.' in str:
            str = str.replace('.', '') # remove all '.'s
        result = int(str)
        return result

if __name__ == "__main__":
    
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser(description=f'Scrape real estate listings from <TODO>')
    parser.add_argument('--debug', action='store_true', help='debug')
    parser.add_argument('--convert', help='convert from v1 to v2')
    
    args = parser.parse_args()
    logging.debug(args)    
 
    if args.debug:
        o = scraperrun.read_json('run_2021-12-12_22-0-58.json')
        o.print_stats()
        exit(1)
    
    if args.convert:
        logging.info(args.convert)
        
        nr_files_read = 0

        for filename in glob.glob('willhaben_*.json'):
            logging.info(filename)
            
            try:
                # get date from filename v1
                m = re.findall('willhaben_(.*)\.json', filename)
                
                # create datetime object, filename v1 contains timestamp
                ts = datetime.datetime.strptime(m[0], '%Y-%m-%d_%H-%M')

                # read json file
                data = None
                with open(filename) as f:
                    data = json.load(f)
                
                props = {}
                for p in data:
                    props[p['willhaben_id']] = prop(p['willhaben_id'], p['url'], p['title'], p['price'], p['squarefeet'])
                
                # init scraperrun object
                v1run = scraperrun('https://www.willhaben.at/iad/immobilien/mietwohnungen/oberoesterreich/linz')
                v1run.props = props
                v1run.ts_start = ts
                v1run.ts_end = ts + datetime.timedelta(minutes=10)
                v1run.max_results = 2000
                
                v1run.print_stats()
                
                # copy titles into array for sequential iterating
                titles = []
                for k, p in v1run.props.items():
                    titles.append(p.title)
                
                # check each title vs. all other titles for similarity
                nr_titles = len(titles)
                dupes = 0
                similarity_cutoff = 0.90
                
                for i in range(nr_titles-1):
                    for j in range(i, nr_titles-1):
                        r = Levenshtein.ratio(titles[i], titles[j+1])
                        if r > similarity_cutoff:
                            dupes += 1
                            logging.debug(f'{i} x {j+1}: {r:.4f}')
                            logging.debug(titles[i])
                            logging.debug(titles[j+1])
                            logging.debug('-')
                
                print(f'Similarity score >{similarity_cutoff}: {dupes} of {nr_titles} ({((dupes/nr_titles)*100):.2f}%)')

                print('---')
                nr_files_read += 1
                if nr_files_read > 20:
                    break
            
            except IndexError:
                logging.error(f'Cannot convert {filename}')

        exit(1)
    
    sr = scraperrun('https://www.willhaben.at/iad/immobilien/mietwohnungen/oberoesterreich/linz?page=1&rows=100', 3)
    sr.start_run()
    sr.end_run()

    sr.print_stats()
    sr.write_json()
    
    str = jsonpickle.encode(sr)
    print(str)
    
    sr.write_json('.')