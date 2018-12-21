import os
from glob import glob
import sys
from io import BytesIO

import time

from dateutil import parser

import pandas as pd
import numpy as np

import swifter
import numba
from multiprocessing import Pool, cpu_count
import random

import nltk
from nltk.sentiment import vader

from libs.writing_utils import get_locations, get_logger
from libs.reading_utils import cleanData

sys.path.append(os.path.dirname(get_locations()[1]))

def applyVader(x, analyzer):
    return analyzer.polarity_scores(x)['compound']

def applyParallel(dfGrouped, func):
    with Pool(cpu_count()) as p:
        ret_list = p.map(func, [group for name, group in dfGrouped])
        
    return pd.DataFrame(ret_list)

def merge_csvs(files, ignore_name=None):
    '''
    Appends csvs and returns

    Parameters:
    ___________

    files (List):
    List of files to append

    Returns:
    ________
    combined (BytesIO):
    BytesIO of the files. Returns None if there is no file
    '''
    combined = BytesIO()
    first = 1
    all_dates = []

    if ignore_name != None:
        ignored_files = [file for file in files if ignore_name not in file] 
    else:
        ignored_files = files

    if len(ignored_files) >= 1:
        for file in ignored_files:
            all_dates.extend(os.path.splitext(os.path.basename(file))[0].split("_"))

            with open(file, "rb") as f:
                if (first != 1):
                    next(f)                
                else:
                    first = 0
                
                combined.write(f.read())

        combined.seek(0)

        # all_dates = sorted(all_dates, key=lambda x: parser.parse(x))
        # all_dates = sorted(all_dates, key=lambda d: tuple(map(int, d.split('-'))))
        
        return combined
    else:
        return None

        
class historicProcessor:
    '''
    Processor for historic data
    '''

    def __init__(self, detailsList, algo_name, relative_dir=""):
        '''
        Parameters:
        ___________
        detailsList (list): 
        List containing keyword, coinname in string and start and end in date format. For looping

        algo_name (string):
        The name of the algorithm so as to save in file

        relative_dir (string):
        The relative directory 
        '''
        _, currRoot_dir = get_locations()

        self.logger = get_logger(os.path.join(currRoot_dir, "logs/historicprocess.log"))

        self.detailsList = detailsList
        self.algo_name = algo_name

        self.historic_path = os.path.join(currRoot_dir, relative_dir, "data/tweet/{}/historic_scrape")

    def read_merge(self, delete=True):
        '''
        Reads many csv files and combines them to one

        Paramters:
        _________
        delete (boolean): Deletes the read file later if set to true
        '''

        for coinDetail in self.detailsList:
            path = os.path.join(self.historic_path.format(coinDetail['coinname']), "raw")

            files = glob(path + "/*")
            f = merge_csvs(files, ignore_name="combined")

            if f != None:
                if (delete==True):
                    for file in files:
                        os.remove(file)

                with open(os.path.join(path, "combined.csv"), "wb") as out:
                    out.write(f.read())

    def clean_data(self):
        '''
        Cleans the csv file. Fillna, drop duplicates and such
        '''
        for coinDetail in self.detailsList:
            fileRead = os.path.join(self.historic_path.format(coinDetail['coinname']), "raw/combined.csv")
            
            if (os.path.isfile(fileRead)):
                df = pd.read_csv(fileRead)
                df = df.dropna().sort_values('Likes', ascending=False).drop_duplicates('ID').sort_values('Time').reset_index(drop=True)
                df.to_csv(fileRead, index=None)
                self.logger.info("Saved cleaned data to {}".format(fileRead))

class livestorageProcessor:
    def __init__(self, keywords, algo_name, relative_dir=""):
        '''
        Parameters:
        ___________
        keywords (dictionary):
        Dictionary containing coinname and its relevant keywords
        Example:
        {'bitcoin': ['bitcoin', 'BTC'], 'dashcoin': ['dashcoin', 'DASH', 'darkcoin']}

        algo_name (string):
        The name of the algorithm so as to save in file

        relative_dir (string):
        The relative directory 
        '''
        _, currRoot_dir = get_locations()

        try:
            self.logger = get_logger(os.path.join(currRoot_dir, "logs/liveprocess.log"))
        except:
            pass

        self.keywords = keywords
        self.algo_name = algo_name

        self.live_path = os.path.join(currRoot_dir, relative_dir, "data/tweet/{}/live_storage")

    def read_merge(self, delete=True):
        '''
        Reads many csv files and combines them to one

        Paramters:
        _________
        delete (boolean): Deletes the read file later if set to true
        '''

        for coinDetail in self.keywords:
            path = self.live_path.format(coinDetail)

            files = [path + "/" + file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]

            f = merge_csvs(files, ignore_name="merged")

            if f != None:
                if (delete==True):
                    for file in files:
                        os.remove(file)

                with open(os.path.join(path, "merged.csv"), "wb") as out:
                    out.write(f.read())
					
    @numba.jit
    def clean_data(self):
        '''
        Cleans the csv file. Fillna, drop duplicates and such
        '''
        for coinDetail in self.keywords:
            fileRead = os.path.join(self.live_path.format(coinDetail), "merged.csv")
            
            if (os.path.isfile(fileRead)):
                print("reading file")
                df = pd.read_csv(fileRead, lineterminator='\n')
                print("file read. Cleaning")
                df = df.dropna().sort_values('Likes', ascending=False).drop_duplicates('ID').sort_values('Time').reset_index(drop=True)
                print("cleaned")
                df.to_csv(os.path.join(self.live_path.format(coinDetail), "cleaned.csv"), index=None)
                os.remove(fileRead)
                print("removed")

class liveProcessor:
    '''
    Processor for live data
    '''

    def __init__(self, keywords, algo_name, relative_dir=""):
        '''
        Parameters:
        ___________
        keywords (dictionary):
        Dictionary containing coinname and its relevant keywords
        Example:
        {'bitcoin': ['bitcoin', 'BTC'], 'dashcoin': ['dashcoin', 'DASH', 'darkcoin']}

        algo_name (string):
        The name of the algorithm so as to save in file

        relative_dir (string):
        The relative directory 
        '''
        _, currRoot_dir = get_locations()

        try:
            self.logger = get_logger(os.path.join(currRoot_dir, "logs/liveprocess.log"))
        except:
            pass

        self.keywords = keywords
        self.algo_name = algo_name

        self.live_path = os.path.join(currRoot_dir, relative_dir, "data/tweet/{}/live")

	
    def read_merge(self, delete=True):
        '''
        Reads many csv files and combines them to one

        Paramters:
        _________
        delete (boolean): Deletes the read file later if set to true
        '''

        for coinDetail in self.keywords:
            path = self.live_path.format(coinDetail)

            files = glob(path + "/*")
            f = merge_csvs(files, ignore_name="combined")

            if f != None:
                if (delete==True):
                    for file in files:
                        os.remove(file)

                with open(os.path.join(path, "combined.csv"), "wb") as out:
                    out.write(f.read())
					
    @numba.jit
    def clean_data(self):
        '''
        Cleans the csv file. Fillna, drop duplicates and such
        '''
        for coinDetail in self.keywords:
            fileRead = os.path.join(self.live_path.format(coinDetail), "combined.csv")
            
            if (os.path.isfile(fileRead)):
                print("reading file")
                df = pd.read_csv(fileRead, lineterminator='\n')
                print("file read. Cleaning")
                df = df.dropna().sort_values('Likes', ascending=False).drop_duplicates('ID').sort_values('Time').reset_index(drop=True)
                print("cleaned")
                df.to_csv(os.path.join(self.live_path.format(coinDetail) + "_storage", "combined_cleaned_{}.csv".format(str(int(time.time())))), index=None)
                print("saved")
                os.remove(fileRead)
                print("removed")


class profileProcessor:
    def __init__(self, detailsList, relative_dir=""):
        '''
        Parameters:
        ___________
        detailsList (list): 
        List containing keyword, coinname in string and start and end in date format. For looping

        relative_dir (string):
        The relative directory 
        '''
        _, currRoot_dir = get_locations()

        self.logger = get_logger(os.path.join(currRoot_dir, "logs/profileprocess.log"))
        self.detailsList = detailsList
        self.profile_path = os.path.join(currRoot_dir, relative_dir, "data/profile")

    def clean_data(self):
        '''
        Cleans the csv file. Fillna, drop duplicates and such
        '''
        live_userData_dir = os.path.join(self.profile_path, "live/userData.csv")
        processed_userData_dir = os.path.join(self.profile_path, "storage/raw/userData.csv")

        if (os.path.isfile(live_userData_dir)):
            userData = pd.read_csv(live_userData_dir, low_memory=False)
            
            if (os.path.isfile(processed_userData_dir)):
                userData=pd.concat([userData, pd.read_csv(processed_userData_dir, low_memory=False)])
        else:
            userData = pd.read_csv(processed_userData_dir, low_memory=False)
        
        self.logger.info("User Data Read")


        userData = userData.set_index('username').drop_duplicates().reset_index()


        self.logger.info("All done saving")

        userData.to_csv(processed_userData_dir, index=None)
        self.logger.info("userData.csv has been updated and moved")

        if (os.path.isfile(live_userData_dir)):
            os.remove(live_userData_dir)

        self.logger.info("Deleting userData.csv in the live folder")
        
        userData['username'].to_csv(os.path.join(self.profile_path, "extractedUsers.csv"), index=None)
        self.logger.info("extractedUsers.csv has been updated")

        live_extractedUsers = os.path.join(self.profile_path, "live/extractedUsers.csv")

        if (os.path.isfile(live_extractedUsers)):
            os.remove(live_extractedUsers)
            
        self.logger.info("Deleting extractedUsers.csv in the live folder")

    def make_unique(self):
        df = pd.read_csv(os.path.join(self.profile_path, "extractedUsers.csv"), header=None)
        uniqueDf = pd.DataFrame({'0': pd.Series(list(set(df[0])))})
        uniqueDf.to_csv(os.path.join(self.profile_path, "extractedUsers.csv"), index=None, header=False)


    def create_ml_features(self):
        '''
        Create features from these data
        '''
        pass
