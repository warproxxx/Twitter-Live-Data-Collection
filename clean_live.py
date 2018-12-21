from processor import liveProcessor
from libs.reading_utils import get_keywords

liveKeywords, historicList = get_keywords()
lp = liveProcessor(liveKeywords, "election")
lp.read_merge()
lp.clean_data()
