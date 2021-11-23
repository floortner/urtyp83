# yield keyword explained @ https://stackoverflow.com/questions/231767/what-does-the-yield-keyword-do

import argparse
import requests
import re
import bs4 # for parsing of html requests
import json
from openpyxl import Workbook # for XLS export
from datetime import *

class REObject:
    def __init__(self, url, title):
        self.url = url
        self.title = title
        self.willhaben_id = ''
        self.price = -1
        self.squarefeet = -1
        #self.rooms = -1
        #self.agency = ''
        #first_seen = datetime
    
    def __str__(self):
        return "REObject: % s\n% s EUR, % sm2, willhaben_id: %s" % (self.title, self.price, self.squarefeet, self.willhaben_id)
        
    # convert string containing EUR currency to int (hack, to be improved)
    def string_to_int(str):
        result = 0
        
        if str is not None:
            if ',' in str:
                str = str[0:str.rfind(',')] # ignore beyond first ','
            if '.' in str:
                str = str.replace('.', '') # remove all '.'s
            result = int(str)
        
        return result

class Urtyp83:
    # constants
    prefix = 'https://www.willhaben.at/'
    start_url = 'https://www.willhaben.at/iad/immobilien/mietwohnungen/oberoesterreich/linz?page=1&rows=100'
    block_list = ['518318955', '493482535', '502036847', '502303940', '340792907'] # exclude bogus listings, future: use percentiles
    max_results = 100
    
    # instance members
    reobjects = []
    url_errors = []
    url_blocked = []
    next_page = start_url

    # crawl a single real estate page
    def crawl_re(url):
        res = requests.get(url)
        if res.status_code == 200:
            html = bs4.BeautifulSoup(res.text, 'html.parser')
            
            reobject = REObject(url, html.title.contents[0])
            
            willhaben_id = re.findall('-\d+\/$', url)[0]
            reobject.willhaben_id = willhaben_id[1:-1]
            
            """ soup = html.find_all('div', {'data-testid': 'contact-box-price-box'})
            for s in soup:
                str = re.findall('\d+[\.|,]?\d*[\.|,]?\d*', s.text)[0]
                i = string_to_int(str)
                print(f'price: {i}') """
                    
            soup = html.find_all(text=re.compile('Gesamtmiete inkl. MWSt'))
            if len(soup) > 0:
                str = re.findall('\d+[\.|,]?\d*[\.|,]?\d*', soup[0].parent.parent.text)[0]
                reobject.price = REObject.string_to_int(str)

            soup = html.find_all(text=re.compile('Wohnfläche'))
            if len(soup) > 0:
                    str = re.findall('\d*[,\d*]', soup[0].parent.parent.next_sibling.text)
                    if str is not None:
                        reobject.squarefeet = REObject.string_to_int(str[0])
            else:
                soup = html.find_all(text=re.compile('Nutzfläche'))
                if len(soup) > 0:
                    str = re.findall('\d*[,\d*]', soup[0].parent.parent.next_sibling.text)[0]
                    reobject.squarefeet = REObject.string_to_int(str)
                
            return reobject

    # get next page (pagination)
    def crawl_main(res):
        html = bs4.BeautifulSoup(res.text, 'html.parser')
        
        # get total number or search results
        total_results = html.find_all('h1', {'data-testid': 'result-list-title'})
        total = re.findall('\d*', total_results[0].text.replace('.', ''))[0]
        print(f'Total number of listings: {total}')
        # https://github.com/maksimKorzh/scrapy-tutorials/blob/master/src/willhaben/willhaben.py
        
        # return the URL of the 'next' page
        try:
            soup = html.find_all('a', {'data-testid': 'pagination-top-next-button'})
            for s in soup:
                print(s['href'])
                return s['href']
        except KeyError:
            return None

    # stats
    def print_stats(reobjects, url_errors, url_blocked):
        total_price = 0
        total_squarefeet = 0
        
        for reobject in reobjects:
            total_price = total_price + reobject.price
            total_squarefeet = total_squarefeet + reobject.squarefeet
        
        no_objects = len(reobjects)
        no_errors = len(url_errors)
        no_blocked = len(url_blocked)
        
        print(f'Pages crawled: {no_objects} ({no_errors} errors, {no_blocked} blocked)')

        print(f'Avg price: {total_price/no_objects}')
        print(f'Avg m2: {total_squarefeet/no_objects}')
        print(f'Price per m2: EUR {total_price/total_squarefeet}')

        if no_errors > 0:
            print("Errors:")
            for url_error in url_errors:
                print(url_error)

        if no_blocked > 0:
            print("Blocked:")
            for url_blocked in url_blocked:
                print(url_blocked)

    # write xls
    def write_speadsheet(reobjects):
        wb = Workbook()
        ws = wb.create_sheet('willhaben_crawler', 0) # new sheet is first tab
        
        ws['A1'] = "Preis inkl. MWst"
        ws['B1'] = "m2"
        ws['C1'] = "Preis pro m2"
        ws['D1'] = "Beschreibung"
        ws['E1'] = "Link auf willhaben.at"

        row = 2
        
        for reobject in reobjects:
            ws["A"+str(row)] = reobject.price
            ws["B"+str(row)] = reobject.squarefeet
            if(reobject.squarefeet > 0):
                ws["C"+str(row)] = reobject.price / reobject.squarefeet
            ws["D"+str(row)] = reobject.title
            ws["E"+str(row)] = reobject.url
            row = row + 1
        
        d = datetime.now()
        fname = f'willhaben_{d.year}-{d.month}-{d.day}_{d.hour}-{d.minute}.xlsx'
        wb.save(fname)
        return fname

    # write json
    def write_json(reobjects):
        d = datetime.now()
        fname = f'willhaben_{d.year}-{d.month}-{d.day}_{d.hour}-{d.minute}.json'
        json_file = open(fname, 'w')
        
        j = json.dumps(reobjects, default=vars)
        
        json_file.write(j)
        return fname

    # write html
    def write_html(html, fname):
        html_file = open(fname, 'wb')

        for chunk in html.iter_content(100000):
            html_file.write(chunk)

        html_file.close()
        print(f'File written: {html_file.name}')

    # main -------------------------------------------------------------
    def letsgo(self):
        i = 0

        res = requests.get(self.next_page)
        if res.status_code == 200:
            
            urls = re.findall('\"\/iad\/immobilien\/d\/.*?\/\"', res.text) # https://regex101.com
            
            for u in urls:
                url = Urtyp83.prefix + u[1:-1]
                print(f'{i}: {url}')
                try:
                    reobject = Urtyp83.crawl_re(url)
                    
                    if reobject.willhaben_id not in Urtyp83.block_list:
                        self.reobjects.append(reobject)
                        print(reobject)
                        print('---')
                    else:
                        self.url_blocked.append(url)        
                    
                except IndexError:
                    self.url_errors.append(url)
                except AttributeError:
                    self.url_errors.append(url)

                i = i+1
                if i >= Urtyp83.max_results:
                    break

            self.next_page = Urtyp83.crawl_main(res)
            return i

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f'Scrape real estate listings from {Urtyp83.start_url}')
    parser.add_argument('--xls', action='store_true', help='store results in willhaben.xlsx')
    parser.add_argument('--json', action='store_true', help='store results in json willhaben.json')
    args = parser.parse_args()
    
    ur = Urtyp83()
    print(f'{ur.letsgo()} pages') # TODOOOOOOOOOOO
    
    Urtyp83.print_stats(ur.reobjects, ur.url_errors, ur.url_blocked)
        
    if args.xls:
        print(f'File written: {Urtyp83.write_speadsheet(ur.reobjects)}')

    if args.json:
        print(f'File written: {Urtyp83.write_json(ur.reobjects)}')
        
    #write_html(res, 'willhaben.hmtl')