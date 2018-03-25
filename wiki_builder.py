#!/usr/bin/env python3

import argparse
import csv
import datetime
import enum
import itertools
import logging
import re
import time

from collections import OrderedDict
from pathlib import Path

import reddit_secret
import praw
from praw.models import Submission


class LevelTypes(enum.IntEnum):
    NORMAL = 0
    PRODUCTION = 1
    TITLE = 2

class Score:
    def __init__(self, a, b, c, link):
        self.stats = (a, b, c)
        self.link = link
    
    def __getitem__(self, key):
        return self.stats[key]

    def __str__(self):
        block = '/'.join(map(str, self.stats))
        if self.link is None:
            return block
        else:
            return f'[{block}]({self.link})'
    
    _pattern = re.compile(r'(\d+)/(\d+)/(\d+)(?: (.+\..+))?')
    @classmethod
    def parse(cls, string):
        match = cls._pattern.match(string)
        if match:
            return cls(int(match[1]), int(match[2]), int(match[3]), match[4])
        else:
            return None
    
    @classmethod
    def fromFourStr(cls, cost, cycles, third, fourth, level_type, link):
        if (fourth is None or level_type != LevelTypes.PRODUCTION):
            return cls(int(cost), int(cycles), int(third), link)
        else:
            return cls(int(cost), int(cycles), int(fourth), link)
    
    def compactStr(self):
        block = '/'.join(map(str, self.stats))
        if self.link is None:
            return block
        else:
            return f'{block} {self.link}'
    
    def simpleStr(self):
        return '/'.join(map(str, self.stats))
    
    def dominates(self, other):
        for s1, s2 in zip(self.stats, other.stats):
            if s1 > s2:
                return False
        if self.stats == other.stats:
            return bool(self.link) >= bool(other.link)
        else:
            return True

class OutputScores:
    def __init__(self, level_type):
        self.level_type = level_type
        self.frontierStr = None
        # A -> B -> C
        self.tripleScores = [[None]*3 for i in range(3)]
        # A -> B*C
        self.prodScores = [None]*3
        # A+B+C
        self.sumScore = None
    
    @staticmethod
    def lessTriple(s1, s2, idx1, idx2):
        idx3 = 0 + 1 + 2 - idx1 - idx2
        return s2 is None or \
               (s1[idx1] < s2[idx1] or
                (s1[idx1] == s2[idx1] and
                 (s1[idx2] < s2[idx2] or
                  (s1[idx2] == s2[idx2] and
                   (s1[idx3] < s2[idx3] or
                    (s1[idx3] == s2[idx3] and
                     bool(s1.link) > bool(s2.link)
                    )
                   )
                  )
                 )
                )
               )
    
    @staticmethod
    def lessProd(s1, s2, idx1):
        idx2, idx3 = (i for i in [0,1,2] if i != idx1)
        return s2 is None or \
               (s1[idx1] < s2[idx1] or
                (s1[idx1] == s2[idx1] and
                 (s1[idx2]*s1[idx3] < s2[idx2]*s2[idx3] or
                  (s1[idx2]*s1[idx3] == s2[idx2]*s2[idx3] and
                   bool(s1.link) > bool(s2.link)
                  )
                 )
                )
               )
    
    @staticmethod
    def lessSum(s1, s2):
        return s2 is None or \
               (sum(s1) < sum(s2) or
                (sum(s1) == sum(s2) and
                 bool(s1.link) > bool(s2.link)
                )
               )
    
    def add(self, s):
        for i,j in itertools.product(range(3), repeat=2):
            if i == j:
                continue
            if (OutputScores.lessTriple(s, self.tripleScores[i][j], i, j)):
                self.tripleScores[i][j] = s
        for i in range(3):
            if (OutputScores.lessProd(s, self.prodScores[i], i)):
                self.prodScores[i] = s
        if (OutputScores.lessSum(s, self.sumScore)):
            self.sumScore = s
    
    def __str__(self):
        
        def unique_and_clean(seq):
            seen = set()
            return [x for x in seq if x and not (x in seen or seen.add(x))]
    
        blob = ''
        scorescols = [
            unique_and_clean(self.tripleScores[0]),
            unique_and_clean(self.tripleScores[1]),
            unique_and_clean(self.tripleScores[2]),
            [self.sumScore] if self.sumScore else []
        ]
        
        printed_prodScore = [False]*3
        
        for row in range(3): # A->B, A->C, A->B*C
            if row > 0:
                blob += '|'
            for col in range(4): # C, C, T, S
                blob += '|'
                if len(scorescols[col]) > row:
                    blob += str(scorescols[col][row])
                    if col <= 2 and scorescols[col][row] == self.prodScores[col]:
                        blob += '*'
                        printed_prodScore[col] = True
                elif col <= 2 and printed_prodScore[col] is False:
                    blob += str(self.prodScores[col]) + '*'
                    printed_prodScore[col] = True
                
            blob += '\n'
        
        return blob

class LevelScores:
    def __init__(self, level_type):
        self.level_type = level_type
        self.scores = []
        
    def add(self, newscore):
        new_scores = []
        for oldscore in self.scores:
            if oldscore.dominates(newscore):
                return
            if not newscore.dominates(oldscore):
                new_scores.append(oldscore)
        
        new_scores.append(newscore)
        self.scores = sorted(new_scores, key=lambda s: s.stats)
        
    def scores_compactStr(self):
        return '' if not self.scores else scores_delim.join(score.compactStr() for score in self.scores)
        
    def scores_simpleStr(self):
        return '' if not self.scores else ' '.join(score.simpleStr() for score in self.scores)


def stringlevels(outputLevels):
    """
    **Golden Thread**|30/445/351*|150/49/199|100/266/48*|205/49/81*
    |||220/49/77||
    |||205/49/81*||
    """
    blob = ''
    
    for level, scores in outputLevels.items():
        if scores.level_type == LevelTypes.TITLE:
            blob +='\n'
            blob += f'##{level}\n\n'
            blob += f'Name|Cost|Cycles|Area|Sum\n:-|:-|:-|:-|:-\n'
        
        else: # regular level
            blob += f'[**{level}**](##Frontier: {scores.frontierStr}##)'
            blob += str(scores)
        
    return blob
        

"""
Solution submission syntax

<puzzle name> : <score1>, <score2>, <score3>, ...

Scores should be of any of the following formats

<Cost>/<Cycles>/<Area>
<Cost>/<Cycles>/<Instructions>
<Cost>/<Cycles>/<Area>/<Instructions>
"""

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.zip_longest(a, b)


trusted_users = set()
levels = OrderedDict()

scores_delim = ' - '

def init(args):
    
    infile = 'levels.csv'
    
    if args.load_scores and Path('scores.csv').is_file():
        infile = 'scores.csv'
    
    with open(infile, 'r') as levelscsv:
        reader = csv.DictReader(levelscsv, skipinitialspace=True)
        for row in reader:
            level_type = LevelTypes(int(row['type']))
            scores = LevelScores(level_type)
            if (level_type != LevelTypes.TITLE):
                for score in filter(None, (Score.parse(s) for s in row['scores'].split(scores_delim))):
                    scores.add(score)
            levels[row['name']] = scores
    
    with open('trusted_users.txt', 'r') as usersfile:
        for user in filter(None, usersfile.read().split('\n')):
            trusted_users.add(user)
    
    logging_level = getattr(logging, args.loglevel)
    logging.basicConfig(level=logging_level)

def load_timestamp():
    try:
        tfile = open('timestamp.utc', 'r')
        return float(tfile.read())
    except FileNotFoundError:
        return 0

def parse_reddit(reddit, last_timestamp, args):
    
    submission = reddit.submission(id='7scj7i')
    submission.comment_sort = 'new'
    submission.comments.replace_more(limit=None)
    
    # I hate user input
    def normalize(string):
        return string.lower().replace('-', ' ').replace('’', "'")
    
    # REGEX!
    sep = r'[\s\*]*/[\s\*]*'
    score_reg = fr'\d+{sep}\d+{sep}\d+(?:{sep}\d+)?'
    pipe_sep_norm_levels = '|'.join(map(normalize, levels))
    good_normalized_line_patt = re.compile(fr'(?P<levelname>{pipe_sep_norm_levels})\W+?{score_reg}(?!.*?{pipe_sep_norm_levels})')

    score_pieces_patt = re.compile(fr'(\d+){sep}(\d+){sep}(\d+)(?:{sep}(\d+))?')
    link_patt = re.compile(r'\]\((.+\..+)\)')
    
    # iterate comments
    for comment in submission.comments.list():
        if not args.trust_everybody and comment.author.name not in trusted_users:
            continue
        
        comment_ts = comment.created_utc
        if comment.edited:
            comment_ts = comment.edited
        if comment_ts <= last_timestamp:
            continue
        
        for line in filter(None, comment.body.splitlines()):
            m = good_normalized_line_patt.search(normalize(line))
            if m: # this is a good line, with one level and some scores, now let's start parsing
                logging.info("Y: %s", line)
                level = None
                for name in levels: # ignore case
                    if normalize(name) == m['levelname']:
                        level = name
                        break
                lev_scores = levels[level]
                
                # we'll define a `score` and link` matches and pair each link with the score that just precedes it
                for m1, m2 in pairwise(score_pieces_patt.finditer(line)):
                    lstart = m1.end()
                    lend = m2.start() if m2 else None
                    linkmatch = link_patt.search(line[lstart:lend])
                    link = None
                    if linkmatch:
                        link = linkmatch[1]
                    score = Score.fromFourStr(*m1.groups(), lev_scores.level_type, link)
                    lev_scores.add(score)
            else:
                logging.info("N: %s", line)

if __name__ == '__main__':
    
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--trust-everybody", action="store_true")
    argparser.add_argument("--no-load-timestamp", action="store_false", dest='load_timestamp')
    argparser.add_argument("--no-load-scores", action="store_false", dest='load_scores')
    argparser.add_argument("--no-parse-reddit", action="store_false", dest='parse_reddit')
    argparser.add_argument("--no-post", action="store_false", dest='post')
    argparser.add_argument("--no-print", action="store_false", dest='print')
    argparser.add_argument("--loglevel", choices=['WARNING', 'INFO', 'DEBUG'], default='WARNING')
    args = argparser.parse_args()

    init(args)
    
    # load timestamps
    last_timestamp = 0
    if args.load_timestamp:
        last_timestamp = load_timestamp()
    current_timestamp = time.time()
    
    # hi reddit
    reddit = praw.Reddit(client_id=reddit_secret.client_id,
                         client_secret=reddit_secret.client_secret,
                         user_agent='OM_Wiki_Crawler',
                         username=reddit_secret.username,
                         password=reddit_secret.password)
    
    if args.parse_reddit:
        parse_reddit(reddit, last_timestamp, args)
    
    # write timestamp
    with open('timestamp.utc', 'w') as tfile:
        tfile.write(str(current_timestamp))
    
    # write result on disk
    with open('scores.csv', 'w') as levelscsv:
        writer = csv.writer(levelscsv)
        writer.writerow(['name', 'type', 'scores'])
        for name, level in levels.items():
            output = [name, str(int(level.level_type)), level.scores_compactStr()]
            writer.writerow(output)
    
    # prepare output
    outputLevels = OrderedDict()
    for name, level in levels.items():
        out_sc = OutputScores(level.level_type)
        if level.scores is not None:
            for score in level.scores:
                out_sc.add(score)
            out_sc.frontierStr = level.scores_simpleStr()
        outputLevels[name] = out_sc
    
    table = stringlevels(outputLevels)
    if args.print:
        print(table)
    
    if args.post:
        # build body
        body = ''
        with open('prefix.md') as prefixfile:
            body += prefixfile.read()
        body += table
        body += f'\nTable built on {datetime.datetime.utcfromtimestamp(current_timestamp)} UTC\n'
        with open('suffix.md') as suffixfile:
            body += suffixfile.read()
        
        # Post to reddit
        post = Submission(reddit, id='86takc')
        post.edit(body)
        
