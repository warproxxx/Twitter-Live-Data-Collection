import threading
import os
import shutil

import time
import datetime
from dateutil.relativedelta import relativedelta

import pandas as pd
import numpy as np

from libs.reading_utils import get_keywords, get_proxies, get_custom_keywords
from libs.writing_utils import get_logger, get_locations
from processor import historicProcessor, profileProcessor, liveProcessor

from twitterscraper import query_historic_tweets
from livescraper import query_live_tweets


def download_live(keywords, logger):
    qt = query_live_tweets(keywords)
    listener, auth = qt.get_listener(create=True)

    while True:
        try:
            qt.perform_search()
        except KeyboardInterrupt:
            logger.warning("Keyboard interrupted. Saving whatever has been collected")
            df, userData, start_time = listener.get_data()
            t1 = threading.Thread(target=qt.save_data, args=[df, userData, start_time, int(time.time())])
            t1.start()
            break
        except Exception as e:
            logger.warning(('Got an exception. Error is: {}. Saving whatever exists').format(str(e)))    
            df, userData, start_time = listener.get_data()

            try:
                qt.save_data(df, userData, start_time, int(time.time()))
            except Exception as e:
                logger.warning(('Got an exception while saving {}').format(str(e)))
                break
    
    download_live(keywords, logger)
    

class runAll:
    def __init__(self, keywords, historicList, proxies, relative_dir=""):
        '''
        Runs everything for twitter

        Parameters:
        ___________

        keywords:

        historicList:

        proxies:

        
        relative_dir:

        '''
        _, currRoot_dir = get_locations() 
        self.relative_dir = relative_dir
        self.currDir = os.path.join(currRoot_dir, relative_dir)
        self.historic_path = os.path.join(self.currDir, "data/tweet/{}/historic_scrape")

        self.logger = get_logger(self.currDir + '/logs/live_utils.txt')
        self.coins = [key for key, value in keywords.items()]
        self.historicList = historicList
        self.proxies = proxies
        
    def initial_houskeeping(self, clean):
        '''
        Cleans the folders
        '''
        if (clean == True):
            self.remove_directory_structure()

        self.create_directory_structure()    

    def create_directory_structure(self):
        self.logger.info("Creating profile directories in case they don't exist")
        
        # os.makedirs("{}/data/profile/storage/raw".format(self.currDir), exist_ok=True)
        # os.makedirs("{}/data/profile/storage/interpreted".format(self.currDir), exist_ok=True)
        os.makedirs("{}/data/profile/live".format(self.currDir), exist_ok=True)
        
        for coinname in self.coins:
            os.makedirs("{}/data/tweet/{}/live".format(self.currDir, coinname), exist_ok=True)
            self.logger.info("Recreating path {}/data/tweet/{}/live if it dosen't exist".format(self.currDir, coinname))
            
            os.makedirs("{}/data/tweet/{}/historic_scrape/raw".format(self.currDir, coinname), exist_ok=True)
            self.logger.info("Recreating path {}/data/tweet/{}/historic_scrape/raw if it dosen't exist".format(self.currDir, coinname))
            os.makedirs("{}/data/tweet/{}/historic_scrape/interpreted".format(self.currDir, coinname), exist_ok=True)
            self.logger.info("Recreating path {}/data/tweet/{}/historic_scrape/interpreted if it dosen't exist".format(self.currDir, coinname))
            
            
            # os.makedirs("{}/data/tweet/{}/live_storage/interpreted/top_raw".format(self.currDir, coinname), exist_ok=True)
            # self.logger.info("Recreating path {}/data/tweet/{}/live_storage/interpreted/top_raw".format(self.currDir, coinname))
            # os.makedirs("{}/data/tweet/{}/live_storage/interpreted/features".format(self.currDir, coinname), exist_ok=True)
            # self.logger.info("Recreating path {}/data/tweet/{}/live_storage/interpreted/features".format(self.currDir, coinname))
            # os.makedirs("{}/data/tweet/{}/live_storage/interpreted/network".format(self.currDir, coinname), exist_ok=True)
            # self.logger.info("Recreating path {}/data/tweet/{}/live_storage/interpreted/network".format(self.currDir, coinname))
            
            os.makedirs("{}/data/tweet/{}/live_storage/archive".format(self.currDir, coinname), exist_ok=True)       
            self.logger.info("Recreating path {}/data/tweet/{}/live_storage/archive".format(self.currDir, coinname))
		
    def remove_directory_structure(self):
        for coinname in self.coins:
            self.logger.info("Removing {}/data/tweet/{}".format(self.currDir, coinname))
            
            try:
                shutil.rmtree("{}/data/tweet/{}".format(self.currDir, coinname))
            except:
                pass

            self.logger.info("Removing {}/data/profile/{}".format(self.currDir, coinname))

            try:
                shutil.rmtree("{}/data/profile".format(self.currDir, coinname))
            except:
                pass

_, currRoot_dir = get_locations() 
logger = get_logger(currRoot_dir + '/logs/run_live.txt')

liveKeywords, historicList = get_keywords()
proxies = get_proxies()

ra = runAll(liveKeywords, historicList, proxies=proxies)
ra.initial_houskeeping(clean=False) #change when required

t1 = threading.Thread(target=download_live, args=[liveKeywords, logger])
t1.start()

logger2 = get_logger(currRoot_dir + '/logs/run_live_2.txt')

#house folder contains kunai ma nabhako data
while True:
    try:
        time.sleep(3 * 60 * 60)
        liveKeywords, historicList = get_keywords()
        proxies = get_proxies()

        historicList = get_custom_keywords(liveKeywords, datetime.datetime.utcnow()-relativedelta(days=1), datetime.datetime.utcnow())

        qh = query_historic_tweets(historicList)
        qh.perform_search()

        hp = historicProcessor(historicList, "paper")
        hp.read_merge(delete=True)
        hp.clean_data()

        pp = profileProcessor(historicList)
        pp.clean_data()

        lp = liveProcessor(liveKeywords, "election")
        lp.read_merge()
        lp.clean_data()
    except Exception as e:
        logger2.info("Got an error: {}".format(str(e)))
