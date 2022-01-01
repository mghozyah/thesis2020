import urllib3
import json
import csv
import datetime
import pytz
import os
import multiprocessing

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ua = {'user-agent' : 'Mozilla/5.0'}
http = urllib3.PoolManager(headers= ua)

class ShopItem:
    def __init__(self, item_id, shop_id):
        self.item_id        = item_id
        self.shop_id        = shop_id
        self.name           = None
        self.model_name     = None
        self.cat_id         = None
        self.sub_id         = None
        self.sub_sub_id     = None
        self.cat_name       = None
        self.sub_name       = None
        self.sub_sub_name   = None
        self.price          = None
        self.location       = None
        self.sold           = None
        self.model_sold     = None
        self.hist_sold      = None
        self.timestamp      = None

        self._request_item()

    def _request_item(self):
        url = "http://shopee.co.id/api/v2/item/get?itemid={}&shopid={}".format(self.item_id, self.shop_id)
        response = http.request('GET', url)
        json_resp = json.loads(response.data.decode('utf-8'))

        data = json_resp['item']
        self.name = data['name']
        self.sold = data['sold']
        self.hist_sold = data['historical_sold']
        self.location = data['shop_location']
        self.cat_id = data['categories'][0]['catid']
        self.sub_id = data['categories'][1]['catid']
        self.sub_sub_id = data['categories'][2]['catid']
        self.cat_name = data['categories'][0]['display_name']
        self.sub_name = data['categories'][1]['display_name']
        self.sub_sub_name = data['categories'][2]['display_name']

        models = data['models']
        if len(models)>0:
            for b in range(len(models)):
                self.model_name = models[b]['name']
                self.price = models[b]['price']/100000
                self.model_sold = models[b]['sold']

                self.write()
        else:
            self.price = data['price']/100000
            self.write()


    def write(self):
        _dir = os.getcwd()
        date = datetime.datetime.now(pytz.timezone("Asia/Jakarta")).strftime('%d-%B-%Y')
        detail_dir = os.path.join(_dir, 'ayolah\\{}'.format(date))

        if not os.path.exists(detail_dir):
            print("Creating folder Detail")
            os.makedirs(detail_dir)

        path = os.path.join(detail_dir, "scraped_by_basket_komoditas.csv")

        self.timestamp  = datetime.datetime.now(pytz.timezone("Asia/Jakarta")).strftime('%H:%M:%S, %d-%B-%Y')

        field = [self.item_id, self.shop_id, self.name, self.model_name, self.cat_id, self.cat_name, self.sub_id, self.sub_name, self.sub_sub_id, self.sub_sub_name, self.price, self.location, self.sold, self.model_sold, self.hist_sold, self.timestamp]
        
        if not os.path.isfile(path):
            with open(path, mode = 'w', encoding='utf-8', newline = '') as csvfile:
                writer = csv.writer(csvfile, delimiter = ';')
                writer.writerow(['item_id', 'shop_id', 'name', 'model_name', 'cat_id', 'cat_name', 'sub_id', 'sub_name', 'sub_sub_id', 'sub_sub_name', 'price', 'location', 'sold', 'model_sold', 'hist_sold', 'timestamp'])
                writer.writerow(field)
        else:
            with open(path, mode = 'a', encoding='utf-8', newline = '') as csvfile:
                writer = csv.writer(csvfile, delimiter = ';')
                writer.writerow(field)

def start(item_id, shop_id):
    ShopItem(item_id, shop_id)

def Search(keyword):
    i = 0
    url = "https://shopee.co.id/api/v2/search_items/?by=relevancy&keyword={}&limit=100&newest={}&order=desc&page_type=search&version=2".format(keyword, i)
    response = http.request('GET', url)
    jeson = json.loads(response.data.decode('utf-8'))

    while(i<2000 and jeson['error']==None):
        data = jeson['items']

        for b in range(len(data)):
            itemid = data[b]['itemid']
            shopid = data[b]['shopid']
            start(itemid, shopid)

        i = i + 100
        url = "https://shopee.co.id/api/v2/search_items/?by=relevancy&keyword={}&limit=100&newest={}&order=desc&page_type=search&version=2".format(keyword, i)
        response = http.request('GET', url) 
        jeson = json.loads(response.data.decode('utf-8'))
        print("keyword: ",keyword, ", iterator: ", i)

if __name__ == '__main__':
    keywords = []

    with open("basket_komoditas_fungsi_what.csv", 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            keywords.append(row[0]) 

    pool = multiprocessing.Pool(processes = 20)

    r = pool.map_async(Search, keywords)
    r.wait()
    print("Done")
