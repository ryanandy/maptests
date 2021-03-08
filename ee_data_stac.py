from __future__ import print_function
import requests
import subprocess
import os
import json
import time
import csv
import urllib
from datetime import datetime
from bs4 import BeautifulSoup

os.chdir(os.path.dirname(os.path.realpath(__file__)))
jpath=os.path.dirname(os.path.realpath(__file__))
now = datetime.now()
infile=os.path.join(jpath,'catalog.json')

idrun=[]
def tdiff():
    # Get last modification time for file
    modTimesinceEpoc = os.path.getmtime(infile)
    modificationTime = time.strftime('%Y-%m-%d', time.localtime(modTimesinceEpoc))
    return modificationTime==now.strftime('%Y-%m-%d')

def ulink(asset_id):
    asset_uid = asset_id.replace('/', '_')
    asset_url = "https://developers.google.com/earth-engine/datasets/catalog/{}".format(
        asset_uid)
    thumbnail_url = 'https://mw1.google.com/ges/dd/images/{}_sample.png'.format(
        asset_uid)

    #print(thumbnail_url)

    r = requests.get(thumbnail_url)

    try:
        if r.status_code != 200:
            html_page = urllib.request.urlopen(asset_url)
            soup = BeautifulSoup(html_page, features="html.parser")

            for img in soup.findAll('img'):
                if 'sample.png' in img.get('src'):
                    thumbnail_url = img.get('src')
                    return [asset_url,thumbnail_url]

        return [asset_url,thumbnail_url]
    except Exception as e:
        print(e)

def parseurl(url,outname):
    try:
        response=requests.get(url)
        if response.status_code==200:
            r=response.json()
            gee_id=r['id']
            gee_title=r['title']
            gee_type=r['gee:type']
            gee_start=r['extent']['temporal']['interval'][0][0].split('T')[0]
            if not r['extent']['temporal']['interval'][0][1]==None:
                gee_end=r['extent']['temporal']['interval'][0][1].split('T')[0]
            else:
                gee_end=now.strftime('%Y-%m-%d')
            gee_start_year=gee_start.split('-')[0]
            gee_end_year=gee_end.split('-')[0]
            gee_provider=r['providers'][0]['name']
            gee_tags=r['keywords']
            asset_url,thumbnail_url=ulink(gee_id)
            idrun.append(gee_id)
            print('Processed a total of {} assets'.format(len(idrun)), end='\r')
            with open(outname,'a') as csvfile:
                writer=csv.writer(csvfile,delimiter=',',lineterminator='\n')
                writer.writerow([gee_id,gee_provider,gee_title,gee_start,gee_end,gee_start_year,gee_end_year,gee_type,', '.join(gee_tags),asset_url,thumbnail_url])
            csvfile.close()
    except Exception as e:
        print(e)

def ee_catalog():
    if not os.path.exists(os.path.join(jpath,'release')):
        os.makedirs(os.path.join(jpath,'release'))
    outname=os.path.join(jpath,'release','eed_'+str(now.strftime('%Y-%m-%d'))+'.csv')
    if os.path.exists(infile):
        with open(outname,'w') as csvfile:
            writer=csv.DictWriter(csvfile,fieldnames=["id", "provider", "title", "start_date","end_date", "startyear","endyear","type","tags","asset_url","thumbnail_url"], delimiter=',',lineterminator='\n')
            writer.writeheader()
        obj = requests.get('https://earthengine-stac.storage.googleapis.com/catalog/catalog.json').json()
        try:
            for assets in obj['links']:
                if assets['rel']=='child':
                    parseurl(assets['href'],outname)
        except Exception as e:
            print(e)
ee_catalog()
