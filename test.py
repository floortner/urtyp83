import datetime
import jsonpickle

class prop:
    def __init__(self, id, url, title, price, sqm):
        self.id = id
        self.url = url
        self.title = title
        self.price = price
        self.sqm = sqm
    
    def __str__(self):
        return "id %s %s %s EUR, % s m2" % (self.id, self.title, self.price, self.sqm)

class scraperrun:
    def __init__(self, start_url):
        self.url = start_url
        self.ts_start = None
        self.ts_end = None

        self.props = {
            '123' : prop('1', '', '', '', ''),
            '234' : prop('2', '', '', '', '')}
    
    def start_run(self):
        self.ts_start = datetime.datetime.now()
    
    def end_rund(self):
        self.ts_end = datetime.datetime.now()
    
    def __str__(self):
        return f'url: {self.url} started: {self.ts_start} props: {len(self.props)}'

if __name__ == "__main__":
    
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
