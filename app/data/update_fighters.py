from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import re
import pandas as pd
import psycopg2
import requests
import random
import time
from dateutil import parser
from datetime import datetime
from bs4 import BeautifulSoup
from psycopg2.extras import execute_values
import curl_cffi
from app.data.database import get_db_connection
import sys

class Fighter:
    def __init__(self, name='', link='', pfp_rank=0, div_rank=0, height=0, age=0, reach=0, wins=0, losses=0, total_fights=0, ranked_wins=0, ranked_losses=0, pfp_wins=0, pfp_losses=0, champ_wins=0, champ_losses=0, pfp_champ_wins=0, pfp_champ_losses=0, title_def=0, title_loss=0, ko_wins=0, ko_losses=0, sub_wins=0, sub_losses = 0, total_fight_time=0, strikes_absorbed=0, total_opp_strikes=0, subs_attempted=0, total_head_strikes=0, total_body_strikes=0, total_leg_strikes=0, 
                 total_head_strikes_missed=0, total_body_strikes_missed=0, total_leg_strikes_missed=0, 
                 total_strikes_landed=0, total_strikes_missed=0, takedowns_landed=0, takedowns_attempted=0, opp_takedowns_landed=0, opp_takedowns_attempted=0, win_streak=0, loss_streak=0, last_5_fight_wins=0, last_five_fight_losses=0, knockdowns=0, opp_knockdowns=0):
        self.name = name
        self.link = link
        self.pfp_rank = pfp_rank
        self.div_rank = div_rank
        self.height = height
        self.age = age
        self.reach = reach
        self._wins = wins
        self._losses = losses
        self.total_fights = total_fights
        self.ranked_wins = ranked_wins 
        self.ranked_losses = ranked_losses 
        self.pfp_wins = pfp_wins 
        self.pfp_losses = pfp_losses
        self.champ_wins = champ_wins 
        self.champ_losses = champ_losses
        self.pfp_champ_wins = pfp_champ_wins
        self.pfp_champ_losses = pfp_champ_losses
        self.title_def = title_def
        self.title_loss = title_loss
        self.ko_wins = ko_wins
        self.ko_losses = ko_losses
        self.sub_wins = sub_wins
        self.sub_losses = sub_losses
        self.total_fight_time = total_fight_time
        self.strikes_absorbed = strikes_absorbed
        self.total_opp_strikes = total_opp_strikes
        self.takedowns_landed = takedowns_landed
        self.takedowns_attempted = takedowns_attempted
        self.opp_takedowns_landed = opp_takedowns_landed
        self.opp_takedowns_attempted = opp_takedowns_attempted
        self.subs_attempted = subs_attempted
        self._total_head_strikes = total_head_strikes
        self._total_body_strikes = total_body_strikes
        self._total_leg_strikes = total_leg_strikes
        self._total_head_strikes_missed = total_head_strikes_missed
        self._total_body_strikes_missed = total_body_strikes_missed
        self._total_leg_strikes_missed = total_leg_strikes_missed
        self._total_strikes_landed = total_strikes_landed
        self._total_strikes_missed = total_strikes_missed
        self.win_streak = win_streak
        self.loss_streak = loss_streak
        self.last_5_fight_wins = last_5_fight_wins
        self.last_5_fight_losses = last_five_fight_losses
        self.knockdowns = knockdowns
        self.opp_knockdowns = opp_knockdowns

        # Initial accuracy calculations
        self.update_accuracy()
    @property
    def last_5_fights_win_rate(self):
        return self.last_5_fight_wins / (self.last_5_fight_wins + self.last_5_fight_losses) if (self.last_5_fight_wins + self.last_5_fight_losses) > 0 else 0

    @property
    def wins(self):
        return self._wins
    
    @property
    def StrAcc(self):
        return (self._total_strikes_landed / self._total_strikes_missed) * 100 if self._total_strikes_missed > 0 else 0

    @wins.setter
    def wins(self, value):
        """Update wins and automatically adjust total fights"""
        self._wins = value
        self.update_total_fights()

    @property
    def losses(self):
        return self._losses

    @losses.setter
    def losses(self, value):
        """Update losses and automatically adjust total fights"""
        self._losses = value
        self.update_total_fights()

    def update_total_fights(self):
        """Automatically update total fights based on wins and losses"""
        self.total_fights = self._wins + self._losses

    @property
    def win_rate(self):
        return (self.wins / self.total_fights) * 100 if self.total_fights > 0 else 0

    @property
    def avg_fight_time(self):
        return self.total_fight_time / self.total_fights if self.total_fights > 0 else 0

    @property
    def finish_rate(self):
        finish_wins = self.ko_wins + self.sub_wins
        return (finish_wins / self.wins) * 100 if self.wins > 0 else 0
    
    @property
    def SubAvg(self):
        return (self.subs_attempted / self.total_fight_time) * 15 if self.total_fight_time > 0 else 0
    
    @property
    def TDAvg(self):
        return (self.takedowns_landed / self.total_fight_time) * 15 if self.total_fight_time > 0 else 0
    
    @property
    def TDAcc(self):
        return (self.takedowns_landed / self.takedowns_attempted) * 100 if self.takedowns_attempted > 0 else 0
    
    @property
    def TDDef(self):
        return ((self.opp_takedowns_attempted - self.opp_takedowns_landed) / self.opp_takedowns_attempted) * 100 if self.opp_takedowns_attempted > 0 else 0
    
    @property
    def total_head_strikes(self):
        return self._total_head_strikes

    @total_head_strikes.setter
    def total_head_strikes(self, value):
        self._total_head_strikes = value
        self.update_accuracy()

    @property
    def total_body_strikes(self):
        return self._total_body_strikes

    @total_body_strikes.setter
    def total_body_strikes(self, value):
        self._total_body_strikes = value
        self.update_accuracy()

    @property
    def total_leg_strikes(self):
        return self._total_leg_strikes

    @total_leg_strikes.setter
    def total_leg_strikes(self, value):
        self._total_leg_strikes = value
        self.update_accuracy()

    @property
    def total_head_strikes_missed(self):
        return self._total_head_strikes_missed

    @total_head_strikes_missed.setter
    def total_head_strikes_missed(self, value):
        self._total_head_strikes_missed = value
        self.update_accuracy()

    @property
    def total_body_strikes_missed(self):
        return self._total_body_strikes_missed

    @total_body_strikes_missed.setter
    def total_body_strikes_missed(self, value):
        self._total_body_strikes_missed = value
        self.update_accuracy()

    @property
    def total_leg_strikes_missed(self):
        return self._total_leg_strikes_missed

    @total_leg_strikes_missed.setter
    def total_leg_strikes_missed(self, value):
        self._total_leg_strikes_missed = value
        self.update_accuracy()

    @property
    def total_strikes_landed(self):
        return self._total_strikes_landed

    @total_strikes_landed.setter
    def total_strikes_landed(self, value):
        self._total_strikes_landed = value
        self.update_accuracy()

    @property
    def total_strikes_missed(self):
        return self._total_strikes_missed
    
    @property
    def SLpM(self):
        """Significant Strikes Landed per Minute (SLpM)"""
        return self.total_strikes_landed / self.total_fight_time if self.total_fight_time > 0 else 0
    
    @property
    def StrDef(self):
        return (((self.total_opp_strikes - self.strikes_absorbed)) / self.total_opp_strikes) * 100 if self.total_opp_strikes > 0 else 0
    
    @property
    def SApM(self):
        return self.strikes_absorbed / self.total_fight_time if self.total_fight_time > 0 else 0
    
    # Rel KO Rate = KO's out of only the Wins, useful more for determining win type.
    @property 
    def rel_ko_rate(self):
        return (self.ko_wins / self.wins) * 100 if self.wins > 0 else 0
    
    # Abs KO Rate = KO's out of all the fights, useful more for determining win prob.
    @property
    def abs_ko_rate(self):
        return (self.ko_wins / self.total_fights) * 100 if self.total_fights > 0 else 0
    
    # Rel Sub Rate = Subs out of only the Wins, useful more for determining win type.
    @property 
    def rel_sub_rate(self):
        return (self.sub_wins / self.wins) * 100 if self.wins > 0 else 0
    
    # Abs Sub Rate = Subs out of all the fights, useful more for determining win prob.
    @property
    def abs_sub_rate(self):
        return (self.sub_wins / self.total_fights) * 100 if self.total_fights > 0 else 0
    
    @property
    def SubAcc(self):
        return (self.sub_wins / self.subs_attempted) * 100 if self.subs_attempted > 0 else 0
    
    # I'm not actually sure how this helps but it's relatively highly correlated with winning
    @property
    def win_finish_metric(self):
        return self.win_rate * self.finish_rate
    
    @property
    def aggression_metric(self):
        return ((self.total_strikes_landed + self.total_strikes_missed) + (self.takedowns_attempted)) / self.total_fight_time if self.total_fight_time > 0 else 0
    
    # Percentage of fights lost by KO
    @property
    def ko_risk(self):
        return (self.ko_losses / self.total_fights) * 100 if self.total_fights > 0 else 0
    
    # Percentage of fights lost by KO
    @property
    def sub_risk(self):
        return (self.sub_losses / self.total_fights) * 100 if self.total_fights > 0 else 0
    
    @property
    def knockdown_risk(self):
        return (self.opp_knockdowns / self.total_fights) * 100 if self.total_fights > 0 else 0
    
    @property
    def knockdown_durability(self):
        return (self.opp_knockdowns / self.total_fight_time) if self.total_fight_time > 0 else 0

    @property
    def AggDef_Delta(self):
        return self.aggression_metric - self.StrDef
    
    @property
    def grappling_vs_striking(self):
        return (self.TDAvg / 33.333333333333336 + self.SubAvg / 29.032258064516128) * 0.5 + (self.SLpM / 45.0 + self.rel_ko_rate / 100.0) * 0.5

    @total_strikes_missed.setter
    def total_strikes_missed(self, value):
        self._total_strikes_missed = value
        self.update_accuracy()

    def update_accuracy(self):
        # Calculate accuracy for each part of the body based on the landed and missed strikes
        self.head_strikes_accuracy = (self._total_head_strikes / (self._total_head_strikes + self._total_head_strikes_missed)) * 100 if (self._total_head_strikes + self._total_head_strikes_missed) > 0 else 0
        self.body_strikes_accuracy = (self._total_body_strikes / (self._total_body_strikes + self._total_body_strikes_missed)) * 100 if (self._total_body_strikes + self._total_body_strikes_missed) > 0 else 0
        self.leg_strikes_accuracy = (self._total_leg_strikes / (self._total_leg_strikes + self._total_leg_strikes_missed)) * 100 if (self._total_leg_strikes + self._total_leg_strikes_missed) > 0 else 0

    def to_dict(self):
        return {
                'name': self.name,
                'link': self.link,
                'p4p_rank': self.pfp_rank if self.pfp_rank != 'NR' else 20,
                'div_rank': self.div_rank if self.div_rank != 'NR' else 20,
                'age': self.age,
                'height': self.height,
                'reach': self.reach,
                'wins': self.wins,
                'losses': self.losses,
                'total_fights': self.total_fights,
                'ranked_wins': self.ranked_wins,
                'ranked_losses': self.ranked_losses,
                'p4p_wins': self.pfp_wins,
                'p4p_losses': self.pfp_losses,
                'champion_wins': self.champ_wins,
                'champion_losses': self.champ_losses,
                'p4p_champion_wins': self.pfp_champ_wins,
                'p4p_champion_losses': self.pfp_champ_losses,
                'title_defenses': self.title_def,
                'title_losses': self.title_loss,
                'win_rate': self.win_rate,
                'ko_wins': self.ko_wins,
                'ko_losses': self.ko_losses,
                'ko_risk': self.ko_risk,
                'sub_wins': self.sub_wins,
                'sub_losses': self.sub_losses,
                'sub_risk': self.sub_risk,
                'finish_rate': self.finish_rate,
                'win_streak': self.win_streak,
                'loss_streak': self.loss_streak,
                'last_five_fight_wins': self.last_5_fight_wins,
                'last_five_fight_losses': self.last_5_fight_losses,
                'last_five_fight_win_rate': self.last_5_fights_win_rate,
                'total_fight_time': self.total_fight_time,
                'avg_fight_time': self.avg_fight_time,
                'SLpM': self.SLpM,
                'SApM': self.SApM,
                'StrDef': self.StrDef,
                'TDAvg': self.TDAvg,
                'TDAcc': self.TDAcc,
                'TDDef': self.TDDef,
                'SubAvg': self.SubAvg,
                'total_head_strikes': self.total_head_strikes,
                'total_body_strikes': self.total_body_strikes,
                'total_leg_strikes': self.total_leg_strikes,
                'total_strikes_landed': self.total_strikes_landed,
                'total_strikes_missed': self.total_strikes_missed,
                'StrAcc': self.StrAcc,
                'head_strikes_accuracy': self.head_strikes_accuracy,
                'body_strikes_accuracy': self.body_strikes_accuracy,
                'leg_strikes_accuracy': self.leg_strikes_accuracy,
                'rel_ko_rate': self.rel_ko_rate,
                'abs_ko_rate': self.abs_ko_rate,
                'rel_sub_rate': self.rel_sub_rate,
                'abs_sub_rate': self.abs_sub_rate,
                'SubAcc': self.SubAcc,
                'knockdowns': self.knockdowns,
                'knockdown_risk': self.knockdown_risk,
                'knockdown_durability': self.knockdown_durability,
                'win_finish_metric': self.win_finish_metric,
                'aggression_metric': self.aggression_metric,
                'grappling_vs_striking': self.grappling_vs_striking,
                'AggDef_Delta': self.AggDef_Delta
            }

    def __repr__(self):
        return (f'{self.name},{self.pfp_rank},{self.div_rank},{self.age},{self.height},{self.reach},{self.wins},{self.losses},{self.total_fights},{self.ranked_wins},{self.ranked_losses},{self.pfp_wins},{self.pfp_losses},{self.champ_wins},{self.champ_losses},{self.pfp_champ_wins},{self.pfp_champ_losses},{self.title_def},{self.title_loss},{self.win_rate},{self.ko_wins},{self.ko_losses},{self.ko_risk},{self.sub_wins},{self.sub_losses},{self.sub_risk},{self.finish_rate},{self.win_streak},{self.loss_streak},{self.last_5_fight_wins},{self.last_5_fight_losses},{self.last_5_fights_win_rate},'
                f'{self.total_fight_time},{self.avg_fight_time},{self.SLpM},{self.SApM},{self.StrDef},{self.TDAvg},{self.TDAcc},{self.TDDef},'
                f'{self.SubAvg},{self.total_head_strikes},{self.total_body_strikes},{self.total_leg_strikes},{self.total_strikes_landed},'
                f'{self.total_strikes_missed},{self.StrAcc},{self.head_strikes_accuracy},{self.body_strikes_accuracy},{self.leg_strikes_accuracy},{self.rel_ko_rate},{self.abs_ko_rate},{self.rel_sub_rate},{self.abs_sub_rate},{self.SubAcc},{self.knockdowns},{self.knockdown_risk},{self.knockdown_durability},{self.win_finish_metric},{self.aggression_metric}')

    def __str__(self):
        return (f'Fighter Name: {self.name}\nFighter PFP Rank: {self.pfp_rank}\nFighter Division Rank: {self.div_rank}\nFighter Age: {self.age}\nFighter Height: {self.height}\nFighter Reach: {self.reach}\nFighter Wins: {self.wins}\nFighter Losses: {self.losses}\nFighter Total Fights: {self.total_fights}\nFighter Ranked Wins: {self.ranked_wins}\nFighter Ranked Losses: {self.ranked_losses}\nFighter P4P Wins: {self.pfp_wins}\nFighter P4P Losses: {self.pfp_losses}\nFighter Champion Wins: {self.champ_wins}\nFighter Champion Losses: {self.champ_losses}\nFighter P4P Champion Wins: {self.pfp_champ_wins}\nFighter P4P Champion Losses: {self.pfp_champ_losses}\nFighter Title Defenses: {self.title_def}\nFighter Title Losses: {self.title_loss}\nFighter Win Rate: {self.win_rate}\n'
                f'Fighter KO Wins: {self.ko_wins}\nFighter KO Losses: {self.ko_losses}\nFighter KO Risk: {self.ko_risk}\nFighter Sub Wins: {self.sub_wins}\nFighter Sub Losses: {self.sub_losses}\nFighter Sub Risk: {self.sub_risk}\nFighter Finish Rate: {self.finish_rate}\nFighter Win Streak: {self.win_streak}\nFighter Loss Streak: {self.loss_streak}\nFighter Last 5 Wins: {self.last_5_fight_wins}\nFighter Last 5 Losses: {self.last_5_fight_losses}\nFighter Last 5 Fights Win Rate: {self.last_5_fights_win_rate}\n'
                f'Fighter Total Fight Time: {self.total_fight_time}\nFighter Avg. Fight Time: {self.avg_fight_time}\nFighter SLpM: {self.SLpM}\n'
                f'Fighter SApM: {self.SApM}\nFighter StrDef: {self.StrDef}\nFighter TDAvg: {self.TDAvg}\nFighter TDAcc: {self.TDAcc}\n'
                f'Fighter TDDef: {self.TDDef}\nFighter SubAvg: {self.SubAvg}\nFighter Total Head Strikes: {self.total_head_strikes}\nFighter Total Body Strikes: {self.total_body_strikes}\n'
                f'Fighter Total Leg Strikes: {self.total_leg_strikes}\nFighter Total Strikes Landed: {self.total_strikes_landed}\n'
                f'Fighter Total Strikes Missed: {self.total_strikes_missed}\nFighter Striking Accuracy: {self.StrAcc}\nFighter Head Strikes Accuracy: {self.head_strikes_accuracy}\n'
                f'Fighter Body Strikes Accuracy: {self.body_strikes_accuracy}\nFighter Leg Strikes Accuracy: {self.leg_strikes_accuracy}\nFighter Relative KO Rate: {self.rel_ko_rate}\nFighter Absolute KO Rate: {self.abs_ko_rate}\nFighter Relative Sub Rate: {self.rel_sub_rate}\nFighter Absolute Sub Rate: {self.abs_sub_rate}\nFighter SubAcc: {self.SubAcc}\nFighter Knockdowns: {self.knockdowns}\nFighter Knockdown Risk: {self.knockdown_risk}\nFighter Knockdown Durability: {self.knockdown_durability}\nFighter Win-Finish-Metric: {self.win_finish_metric}\nFighter Aggression Metric: {self.aggression_metric}')

def getRank(name, weightclass, date):
    # parse date just in case
    try:
        date = parser.parse(date)
    except:
        pass
    
    rankings_csv_buffer = StringIO(requests.get('https://raw.githubusercontent.com/martj42/ufc_rankings_history/master/rankings_history.csv').text)
    rankings_df = pd.read_csv(rankings_csv_buffer)
    rankings_df['date'] = rankings_df['date'].apply(parser.parse) # Makes the dates comparable after parsing fight date

    #now,  we need to find the closest date in the dataframe to the actual fight date
    subset = rankings_df[
        (rankings_df['fighter'] == name) &
        (rankings_df['weightclass'] == weightclass) &
        (rankings_df['date'] <= date)
    ]

    # Get the latest ranking before fight date
    if not subset.empty:
        closest_row = subset.sort_values('date', ascending=False).iloc[0]
        rank = f"{closest_row['rank']:02d}"
    else:
        rank = 'NR'

    return rank

def getFighterName(link):
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')
    header = soup.find('h2', class_='b-content__title')
    name = header.find('span', class_='b-content__title-highlight').get_text(strip=True)
    return name

def getElementWithString(soup, tag, class_Attr, string_Attr):
    return soup.find(tag, class_=class_Attr, string=lambda text: text and string_Attr in text.strip())

def getMatchLength(final_round_time, rounds, format):
    final_round_slices = final_round_time.split(':')
    total_time_seconds = int(final_round_slices[0]) * 60 + int(final_round_slices[1])

    try:
        round_lengths = list(map(int, format.strip("()").split("-")))
        try:
            for i in range(int(rounds) - 1):
                total_time_seconds += round_lengths[i] * 60
        except IndexError:
            # Unlimited rounds with specified round time limit
            total_time_seconds += round_lengths[0] * 60 * int(rounds) 
    except ValueError:
        # No time limit/Sectioned rounds, pass.
        pass

    return total_time_seconds / 60

def parseSigStatsTable(table, fighter):
    table_row = table.find('tbody').find('tr')
    cols = table_row.find_all('td')

    curr_name_element = cols[0].find('p')
    curr_name = curr_name_element.get_text(strip=True)
    if curr_name == fighter.name:
        p_index = 0
    elif curr_name_element.find_next('p').get_text(strip=True) == fighter.name:
        p_index = 1

    if p_index == 0:
        # Total Strikes
        sig_strikes_raw = cols[1].find('p').get_text(strip=True)
        sig_slices = sig_strikes_raw.split('of')
        fighter._total_strikes_landed += int(sig_slices[0])
        fighter._total_strikes_missed += int(sig_slices[1])

        # Strikes Absorbed and evaded
        opp_sig_strikes_raw = cols[1].find('p').find_next('p').get_text(strip=True)
        opp_sig_slices = opp_sig_strikes_raw.split('of')
        fighter.strikes_absorbed += int(opp_sig_slices[0])
        fighter.total_opp_strikes += int(opp_sig_slices[1])

        # Head Strikes
        head_strikes_raw = cols[3].find('p').get_text(strip=True)
        head_slices = head_strikes_raw.split('of')
        fighter.total_head_strikes += int(head_slices[0])
        fighter.total_head_strikes_missed += int(head_slices[1])

        # Body Strikes
        body_strikes_raw = cols[4].find('p').get_text(strip=True)
        body_slices = body_strikes_raw.split('of')
        fighter.total_body_strikes += int(body_slices[0])
        fighter.total_body_strikes_missed += int(body_slices[1])

        # Leg Strikes
        leg_strikes_raw = cols[5].find('p').get_text(strip=True)
        leg_slices = leg_strikes_raw.split('of')
        fighter.total_leg_strikes += int(leg_slices[0])
        fighter.total_leg_strikes_missed += int(leg_slices[1])
    elif p_index == 1:
        # Total Strikes
        sig_strikes_raw = cols[1].find('p').find_next('p').get_text(strip=True)
        sig_slices = sig_strikes_raw.split('of')
        fighter._total_strikes_landed += int(sig_slices[0])
        fighter._total_strikes_missed += int(sig_slices[1])

        # Strikes Absorbed and evaded
        opp_sig_strikes_raw = cols[1].find('p').get_text(strip=True)
        opp_sig_slices = opp_sig_strikes_raw.split('of')
        fighter.strikes_absorbed += int(opp_sig_slices[0])
        fighter.total_opp_strikes += int(opp_sig_slices[1])

        # Head Strikes
        head_strikes_raw = cols[3].find('p').find_next('p').get_text(strip=True)
        head_slices = head_strikes_raw.split('of')
        fighter.total_head_strikes += int(head_slices[0])
        fighter.total_head_strikes_missed += int(head_slices[1])

        # Body Strikes
        body_strikes_raw = cols[4].find('p').find_next('p').get_text(strip=True)
        body_slices = body_strikes_raw.split('of')
        fighter.total_body_strikes += int(body_slices[0])
        fighter.total_body_strikes_missed += int(body_slices[1])

        # Leg Strikes
        leg_strikes_raw = cols[5].find('p').find_next('p').get_text(strip=True)
        leg_slices = leg_strikes_raw.split('of')
        fighter.total_leg_strikes += int(leg_slices[0])
        fighter.total_leg_strikes_missed += int(leg_slices[1])
    
def parseNormalTable(table, fighter):
    table_row = table.find('tbody').find('tr')
    cols = table_row.find_all('td')

    curr_name_element = cols[0].find('p')
    curr_name = curr_name_element.get_text(strip=True)
    if curr_name == fighter.name:
        p_index = 0
    elif curr_name_element.find_next('p').get_text(strip=True) == fighter.name:
        p_index = 1

    if p_index == 0:
        # Knockdowns
        knockdowns = cols[1].find('p').get_text(strip=True)
        fighter.knockdowns += int(knockdowns)

        # Opponenent Knockdowns
        opp_knockdowns = cols[1].find('p').find_next('p').get_text(strip=True)
        fighter.opp_knockdowns += int(opp_knockdowns)

        # Takedown Attempts
        takedowns_raw = cols[5].find('p').get_text(strip=True)
        takedowns_slices = takedowns_raw.split('of')
        fighter.takedowns_landed += int(takedowns_slices[0])
        fighter.takedowns_attempted += int(takedowns_slices[1])

        # Opponent Takedown Attempts
        opp_takedowns_raw = cols[5].find('p').find_next('p').get_text(strip=True)
        opp_takedowns_slices = opp_takedowns_raw.split('of')
        fighter.opp_takedowns_landed += int(opp_takedowns_slices[0])
        fighter.opp_takedowns_attempted += int(opp_takedowns_slices[1])        

        # Submission Attempts
        submissions_raw = cols[7].find('p').get_text(strip=True)
        fighter.subs_attempted += int(submissions_raw)

    elif p_index == 1:
        # Knockdowns
        knockdowns = cols[1].find('p').find_next('p').get_text(strip=True)
        fighter.knockdowns += int(knockdowns)

        # Opponenent Knockdowns
        opp_knockdowns = cols[1].find('p').get_text(strip=True)
        fighter.opp_knockdowns += int(opp_knockdowns)

        # Takedown Attempts
        takedowns_raw = cols[5].find('p').find_next('p').get_text(strip=True)
        takedowns_slices = takedowns_raw.split('of')
        fighter.takedowns_landed += int(takedowns_slices[0])
        fighter.takedowns_attempted += int(takedowns_slices[1])

        # Opponent Takedown Attempts
        opp_takedowns_raw = cols[5].find('p').get_text(strip=True)
        opp_takedowns_slices = opp_takedowns_raw.split('of')
        fighter.opp_takedowns_landed += int(opp_takedowns_slices[0])
        fighter.opp_takedowns_attempted += int(opp_takedowns_slices[1])

        # Submission Attempts
        submissions_raw = cols[7].find('p').find_next('p').get_text(strip=True)
        fighter.subs_attempted += int(submissions_raw)

def getWeightclass(link):
    fight_html = requests.get(link, timeout=300)
    soup = BeautifulSoup(fight_html.text, "html.parser")
    # peel the weightclass out of the main string using regex magic
    bout_str = soup.find('i', class_='b-fight-details__fight-title').get_text(strip=True)
    match = re.search(r'(?:UFC\s)?(.*?)\s(?:Title\s)?Bout', bout_str)
    weightclass = match.group(1).strip() if match else None
    return weightclass

def processFight(link, fighter):
    result = ''
    while True:
        try:
            # Store results in a temporary dictionary to prevent duplication issues
            #temp_fighter = Fighter(name=fighter.name, wins=fighter.wins, losses=fighter.losses, ko_wins=fighter.ko_wins, sub_wins=fighter.sub_wins, ko_losses=fighter.ko_losses, sub_losses=fighter.sub_losses, total_fight_time=fighter.total_fight_time, takedowns_attempted=fighter.takedowns_attempted, takedowns_landed=fighter.takedowns_landed, subs_attempted=fighter.subs_attempted, opp_takedowns_landed=fighter.opp_takedowns_landed, opp_takedowns_attempted=fighter.opp_takedowns_attempted, _total_strikes_landed=fighter._total_strikes_landed, _total_strikes_missed=fighter.total_strikes_missed, strikes_absorbed=fighter.strikes_absorbed, total_opp_strikes=fighter.total_opp_strikes, total_head_strikes=fighter.total_head_strikes, total_head_strikes_missed=fighter.total_head_strikes_missed, total_body_strikes=fighter.total_body_strikes, total_body_strikes_missed=fighter.total_body_strikes_missed, total_leg_strikes=fighter.total_leg_strikes, total_leg_strikes_missed=fighter.total_leg_strikes_missed)
            temp_fighter = Fighter(name=fighter.name)

            fight_html = requests.get(link, timeout=300)
            soup = BeautifulSoup(fight_html.text, "html.parser")

            # to find the division ranking, we need to know the weightclass

            # peel the weightclass out of the main string using regex magic
            bout_str = soup.find('i', class_='b-fight-details__fight-title').get_text(strip=True)
            match = re.search(r'(?:UFC\s)?(.*?)\s(?:Title\s)?Bout', bout_str)
            weightclass = match.group(1).strip() if match else None

            # We also need the date of the fight
            event_element = soup.find('h2')
            date_link = event_element.find('a')['href']
            main_page = requests.get(date_link)
            temp_soup = BeautifulSoup(main_page.text, 'html.parser')
            date_raw = temp_soup.find('li', class_="b-list__box-list-item").get_text(strip=True).split(':')[1]
            date = parser.parse(date_raw)

            # First, see if the fighter won, lost, or neither this fight.
            fighter_names = soup.find_all('div', class_='b-fight-details__person-text')
            results = soup.find_all('i', class_='b-fight-details__person-status')
            for fighter_name, result_raw_html in zip(fighter_names, results):
                fighter_name = fighter_name.find('h3').find('a').text.strip()
                if fighter_name == fighter.name:
                    result = result_raw_html.text.strip()
                    rank = getRank(temp_fighter.name, weightclass, date)
                    if result == 'W':
                        temp_fighter.wins += 1
                        win_type = getElementWithString(soup, 'i', 'b-fight-details__label', 'Method:').find_parent().text.strip().split(' ')[-1]
                        if 'KO' in win_type:
                            temp_fighter.ko_wins += 1
                        elif 'Subm' in win_type:
                            temp_fighter.sub_wins += 1
                        if rank == '00':
                            temp_fighter.title_def += 1
                    elif result == 'L':
                        temp_fighter.losses += 1
                        loss_type = getElementWithString(soup, 'i', 'b-fight-details__label', 'Method:').find_parent().text.strip().split(' ')[-1]
                        if 'KO' in loss_type:
                            temp_fighter.ko_losses += 1
                        elif 'Subm' in loss_type:
                            temp_fighter.sub_losses += 1
                        if rank == '00':
                            temp_fighter.title_loss += 1
                    
                else: # We have the opponent for this fight, so can see thier rank and return it with the result like 'W12' or 'W00' or 'WNR'
                    # We can check for pound-for-pound first
                    rank = getRank(fighter_name, weightclass, date)
                    p4p_rank = getRank(fighter_name, 'Pound-for-Pound', date)

                    result = result_raw_html.text.strip()
                    if result == 'L' and rank != 'NR':
                        temp_fighter.ranked_wins += 1
                        if rank == '00':
                            temp_fighter.champ_wins += 1
                    elif result == 'W' and rank != 'NR':
                        temp_fighter.ranked_losses += 1
                        if rank == '00':
                            temp_fighter.champ_losses += 1
                        
                    if result == 'L' and p4p_rank != 'NR':
                        temp_fighter.pfp_wins += 1
                        if p4p_rank == '00': # might be a bug? re-evaluate
                            temp_fighter.pfp_champ_wins += 1
                    elif result == 'W' and p4p_rank != 'NR':
                        temp_fighter.pfp_losses += 1
                        if rank == '00':
                            temp_fighter.pfp_champ_losses += 1
                    
                    # Now we flip the result for the return
                    if result == 'W':
                        result = 'L'
                    elif result == 'L':
                        result = 'W'

            # Next, find the fight format and final round end time to help calculate certain metrics like SLpM and SApM
            round_label = getElementWithString(soup, 'i', 'b-fight-details__label', 'Round:').find_parent().text.strip()
            round = round_label.split(' ')[-1]
            time_label = getElementWithString(soup, 'i', 'b-fight-details__label', 'Time:').find_parent().text.strip()
            last_round_time = time_label.split(' ')[-1]
            time_format_label = getElementWithString(soup, 'i', 'b-fight-details__label', 'Time format:').find_parent().text.strip()
            time_format = time_format_label.split(' ')[-1]
            time_in_min = getMatchLength(last_round_time, round, time_format)
            temp_fighter.total_fight_time += time_in_min
            # Next, find the total significant strikes, both raw and by body area.
            tables = soup.find_all('table', style="width: 745px")
            try:
                totals_table = tables[0] # The first on-screen table with general stats, needed primarily for takedowns
                sig_strike_table = tables[1] # The second on-screen table with significant strike stats
                parseSigStatsTable(sig_strike_table, temp_fighter)
                parseNormalTable(totals_table, temp_fighter)
            except IndexError:
                pass

            break
        except Exception as e:
            # print(str(e) + ", " + str(link)) only needed for debugging
            time.sleep(random.uniform(1.0, 3.0))
    
    fighter.wins += temp_fighter.wins
    fighter.losses += temp_fighter.losses
    fighter.ko_wins += temp_fighter.ko_wins
    fighter.ko_losses += temp_fighter.ko_losses
    fighter.sub_wins += temp_fighter.sub_wins
    fighter.sub_losses += temp_fighter.sub_losses
    fighter.total_fight_time += temp_fighter.total_fight_time
    fighter.takedowns_landed += temp_fighter.takedowns_landed
    fighter.takedowns_attempted += temp_fighter.takedowns_attempted
    fighter.opp_takedowns_landed += temp_fighter.opp_takedowns_landed
    fighter.opp_takedowns_attempted += temp_fighter.opp_takedowns_attempted
    fighter.subs_attempted += temp_fighter.subs_attempted
    fighter._total_strikes_landed += temp_fighter._total_strikes_landed
    fighter._total_strikes_missed += temp_fighter._total_strikes_missed
    fighter.strikes_absorbed += temp_fighter.strikes_absorbed
    fighter.total_opp_strikes += temp_fighter.total_opp_strikes
    fighter.total_head_strikes += temp_fighter.total_head_strikes
    fighter.total_head_strikes_missed += temp_fighter.total_head_strikes_missed
    fighter.total_body_strikes += temp_fighter.total_body_strikes
    fighter.total_body_strikes_missed += temp_fighter.total_body_strikes_missed
    fighter.total_leg_strikes += temp_fighter.total_leg_strikes
    fighter.total_leg_strikes_missed += temp_fighter.total_leg_strikes_missed
    fighter.knockdowns += temp_fighter.knockdowns
    fighter.opp_knockdowns += temp_fighter.opp_knockdowns
    fighter.ranked_wins += temp_fighter.ranked_wins
    fighter.ranked_losses += temp_fighter.ranked_losses
    fighter.pfp_wins += temp_fighter.pfp_wins
    fighter.pfp_losses += temp_fighter.pfp_losses
    fighter.champ_wins += temp_fighter.champ_wins
    fighter.pfp_champ_wins += temp_fighter.pfp_champ_wins
    fighter.pfp_champ_losses += temp_fighter.pfp_champ_losses
    fighter.champ_losses += temp_fighter.champ_losses
    fighter.title_def += temp_fighter.title_def
    fighter.title_loss += temp_fighter.title_loss # Need to implement these in Fighter Class, Header, Remember that result is now 'WNR' or 'W00' for all fights, will need to filter out the numbers and set Division Rank to the number. Do Pound-4-Pound before these.

    return result

def calculateStreaks(result_list):
    result_list.reverse()
    win_streak = 0
    loss_streak = 0
    for result in result_list:
        if result == 'W':
            win_streak += 1
            loss_streak = 0
        elif result == 'L':
            win_streak = 0
            loss_streak += 1
    return (win_streak, loss_streak)

def get_fighter_stats_from_link(fighter_link):
    fight_links = [] # Collection of all the links to each fight this fighter has had before the date
    date = datetime.now() # The cutoff date for fights
    fight_list_html = requests.get(fighter_link, timeout=300) # Response from the fighter's link
    fight_list_html.raise_for_status()  # Ensure the request was successful
    soup = BeautifulSoup(fight_list_html.text, "html.parser")

    # Extract the fighter name for stat collection
    fighter_name = soup.find('span', class_='b-content__title-highlight').get_text(strip=True)
    fighter = Fighter(name=fighter_name)

    # Get age, stat, reach (inches)

    # info_elements: all the elements in the table under the name and nickname, contains all unchanging 
    # fields like height and reach
    info_elements = soup.find_all('li', class_="b-list__box-list-item b-list__box-list-item_type_block")

    # Height
    height_uncov = info_elements[0].get_text(strip=True).replace(' ', '').split(':')[1].split('\'')
    try:
        height = (int(height_uncov[0]) * 12) + int(height_uncov[1][:-1])
    except ValueError:
        height = 70 # Make a guess of 5'10, COULD BE OPTIMIZED LATER
    fighter.height = height

    # Reach
    try:
        reach = int(info_elements[2].get_text(strip=True).replace(' ', '').split(':')[1][:2])
    except:
        # reach was '--'/undefined, assume reach = height.
        reach = height
    fighter.reach = reach

    # Age
    DOB_unparsed = info_elements[4].get_text(strip=True).split(':')[1]
    try:
        DOB_parsed = parser.parse(DOB_unparsed)
        age = date.year - DOB_parsed.year
        if (date.month, date.day) < (DOB_parsed.month, DOB_parsed.year):
            age -= 1
        fighter.age = age
    except:
        fighter.age = 28 # reasonable guess

    # Find all rows with the class "b-fight-details__table-row"
    rows = soup.find_all('tr', class_='b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click')
    result_list = [] # The ordered result (Win / Loss) of each fight

    # Iterate through each row and extract data
    for row in rows:
        # Extract the date first and check if the date is before the specified date
        event_date = row.find_all('p', class_='b-fight-details__table-text')[-5].get_text(strip=True)
        event_date = parser.parse(event_date)
        if (event_date < date):
            fight_link = row['data-link']
            fight_links.append(fight_link)

    # Lets set the current ranks up now
    if len(fight_links) > 0:
        fighter.div_rank = getRank(fighter.name, getWeightclass(fight_links[0]), date)
        fighter.pfp_rank = getRank(fighter.name, 'Pound-for-Pound', date)
    else:
        fighter.div_rank = 'NR'
        fighter.pfp_rank = 'NR'
    
    results_in_order = [None] * len(fight_links) # Keeps the size right for the list, so the thread results go into the right index instead of appending in order of completion

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_index = {
            executor.submit(processFight, link, fighter): idx
            for idx, link in enumerate(fight_links)
        }

        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            result = future.result()
            if result is not None:
                results_in_order[idx] = result
    
    # Filter out any None entries (in case any fight failed to process)
    result_list = [r for r in results_in_order if r is not None]

    streaks = calculateStreaks(result_list) # streaks[0] = win streak, streaks[1] = loss streak.
    fighter.win_streak = streaks[0]
    fighter.loss_streak = streaks[1]


    if len(result_list) >= 5:
        for i in range(len(result_list) - 5, len(result_list)):
            if result_list[i] == 'W':
                fighter.last_5_fight_wins += 1
            elif result_list[i] == 'L':
                fighter.last_5_fight_losses += 1
    else:
        for i in range(len(result_list)):
            if result_list[i] == 'W':
                fighter.last_5_fight_wins += 1
            elif result_list[i] == 'L':
                fighter.last_5_fight_losses += 1

    return fighter

# Gets all the fighter links from a UFCStats.com event.  If there is no specified card link, fighter links from the most recent upcoming card will be returned.
def get_fighters_from_card(card_link=''):
    if card_link == '':
        # Scrape the UFCStats website for the most recent upcoming card.
        response = requests.get("http://ufcstats.com/statistics/events/completed")
        soup = BeautifulSoup(response.text, "html.parser")
        card_link = soup.find('a', class_='b-link b-link_style_white')['href'].strip()
    # Get every fighter from the card link now.
    fighter_links = []
    response = requests.get(card_link)
    soup = BeautifulSoup(response.text, "html.parser")
    matchup_table = soup.find('table')
    rows = matchup_table.find_all('tr')
    for row in rows:
        try:
            col = row.find_all('td')[1]
        except IndexError:
            continue
        fighters = col.find_all('a')
        fighter_link_1 = fighters[0]['href']
        fighter_link_2 = fighters[1]['href']
        fighter_links.append(fighter_link_1)
        fighter_links.append(fighter_link_2)
    return fighter_links

# Get the opening odds of a fight from BestOdds
# 
# Params:
# fighter_1_name, String, the name of the first fighter
# fighter_2_name, String, the name of the second fighter
# date, String, the date of the fight in the format of "April 26, 2025"
#
# Returns:
# tuple(int, int), the odds of the fight with the respective indexes holding the odds in the same order as the the fighter names given.
def getFightOdds(fighter_1_name, fighter_2_name, event_date):
    ODDS_URL = ODDS_URL = 'https://www.bestfightodds.com'
    req_link = ODDS_URL + '/search?query=' + fighter_1_name.replace(' ', '+')
    search_response_html = curl_cffi.get(req_link, impersonate='firefox')
    search_response_html.raise_for_status() # Ensure good connection
    soup = BeautifulSoup(search_response_html.text, 'html.parser')
    rows = soup.find_all('tr')

    fighter_1_link = ''
    for row in rows:
        link_tag = row.find('a')
        if link_tag and link_tag.text.strip() == fighter_1_name:
            fighter_1_link = link_tag['href']  # returns relative URL like "/fighters/Alexander-Volkanovski-9523"
            break
            
    if fighter_1_link != '':
        fight_list_html = curl_cffi.get(ODDS_URL + fighter_1_link, impersonate='firefox', timeout=120)
        soup = BeautifulSoup(fight_list_html.text, 'html.parser')
        rows = soup.find_all('tr')
        fighter_1_odds = 0
        fighter_2_odds = 0
        # Fighter 1's name will always be on top, need to find fighter 2's name and compare
        for i in range(len(rows)):
            text_items = rows[i].find_all('a')
            try:
                for item in text_items:
                    if item.text.strip() == fighter_2_name:
                        date_text = rows[i].find('td', style="padding-left: 20px; color: #767676").get_text(strip=True)
                        # Check if date is within valid range of given date
                        search_date = parser.parse(date_text)
                        distance = abs((event_date - search_date).days)
                        if distance <= 6:
                            # we have the right row for sure, get odds for the row before it (Fighter 1 odds) and this row (Fighter 2 odds)
                            fighter_1_odds = rows[i - 1].find('td', class_='moneyline').get_text(strip=True)
                            fighter_2_odds = rows[i].find('td', class_='moneyline').get_text(strip=True)
                            return (int(fighter_1_odds), int(fighter_2_odds))
                        else:
                            pass # keep searching
            except:
                pass
        return None
    else:
        return None # Could not find fighter 1, no odds.

# Updates the fighters table with all applicable stats excluding opening odds
def update_fighter_data():
    resume_index = 0 # idex to resume at if there's some sort of connection reset error.
    while True:
        try: 
            date = datetime.now()
            # fighter_data_list = list of dictionaries, e.g.:
            # [
            #   {"name": "Fighter A", "age": 30, "height": 180, ...},
            #   {"name": "Fighter B", "age": 32, "height": 175, ...},
            # ]
            fighter_data_list = [] # program getting the data here, rememeber to NOT set odds

            # Get every fighter profile from the UFCStats.com fighters page.
            # print("Getting fighter links...")
            # letters = [chr(i) for i in range(ord('a'), ord('z') + 1)]
            # #letters = [chr(i) for i in range(ord('a'), ord('b') + 1)]
            # fighter_links = []
            # for letter in letters:
            #     response = requests.get(f'http://ufcstats.com/statistics/fighters?char={letter}&page=all')
            #     soup = BeautifulSoup(response.text, 'html.parser')
            #     # Get all the links from the page
            #     results_table = soup.find('table', class_='b-statistics__table')
            #     if results_table == None: 
            #         # Add a sort of error logging function here later
            #         continue
            #     rows = results_table.find_all('tr', class_='b-statistics__table-row')
            #     for row in rows:
            #         link = row.find('a')
            #         if link != None:
            #             fighter_links.append(link['href'])
            #     time.sleep(random.uniform(1, 3)) # Don't overwhelm UFC servers

            # Get all fighters from upcoming card
            fighter_links = get_fighters_from_card()

            # Now that fighter_links contains the links to every profile, we can get the stats, return a dictionary, and append to fighter_data_list
            for link in fighter_links[resume_index:]: # just get the first ten for debugging
                print(f"({resume_index + 1}/{len(fighter_links)}) Getting stats for {link}")
                fighter = get_fighter_stats_from_link(link)
                fighter.link = link
                # Set ranks
                #fighter.div_rank = getRank(fighter.name, getWeightclass(link), date.isoformat())
                if fighter.div_rank == 'NR':
                    fighter.div_rank = '20'
                fighter.div_rank = int(fighter.div_rank)

                #fighter.pfp_rank = getRank(fighter.name, 'Pound-for-Pound', date.isoformat())
                if fighter.pfp_rank == 'NR':
                    fighter.pfp_rank = '20'
                fighter.pfp_rank = int(fighter.pfp_rank)

                fighter_data_list.append(fighter.to_dict())
                time.sleep(random.uniform(1, 3))

                conn = get_db_connection()

                with conn:
                    with conn.cursor() as cur:
                        # Prepare columns and values
                        columns = fighter_data_list[0].keys()
                        values = [[f[col] for col in columns] for f in fighter_data_list]

                        # Build the INSERT ... ON CONFLICT statement
                        insert_query = f"""
                            INSERT INTO fighters ({', '.join(columns)})
                            VALUES %s
                            ON CONFLICT (link) DO UPDATE
                            SET {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'link'])};
                        """

                        execute_values(cur, insert_query, values)
                        print("Updated fighter data.")

                conn.close()
                resume_index += 1
                if resume_index >= len(fighter_links):
                    break
            break
        except Exception as e:
            print(e)
            continue

# Updates the matchups table with with upcoming fighter matchups
def update_matchups(clean=False):
    fighter_links = get_fighters_from_card()

    conn = get_db_connection()

    with conn:
        with conn.cursor() as cur:
            if clean:
                cur.execute("DROP TABLE IF EXISTS matchups;")
                cur.execute("""
                    CREATE TABLE matchups (
                        id SERIAL PRIMARY KEY,
                        fighter_a_id INTEGER,
                        fighter_b_id INTEGER,
                        fighter_a_prediction REAL,
                        fighter_b_prediction REAL
                    );

                    ALTER TABLE matchups
                    ADD CONSTRAINT matchup_id_order CHECK (fighter_a_id < fighter_b_id);

                    ALTER TABLE matchups
                    ADD CONSTRAINT unique_matchup_pair UNIQUE (fighter_a_id, fighter_b_id);
                """)

    for i in range(0, len(fighter_links), 2):
        fighter_1 = fighter_links[i]
        fighter_2 = fighter_links[i + 1]
        #names = []
        #for fighter in fighters:
            #name = getFighterName(fighter)
            #names.append(name)

        with conn:
            with conn.cursor() as cur:
                # Step 1: Get fighter IDs for the two names
                cur.execute(
                    "SELECT id FROM fighters WHERE link = %s OR link = %s;",
                    (fighter_1, fighter_2)#(names[0], names[1])
                )
                results = cur.fetchall()

                # Ensure both names were found
                if len(results) != 2:
                    raise ValueError("One or both fighter names not found in 'fighters' table.")

                # Step 2: Map names to IDs correctly (in case order was switched in the query result)
                cur.execute(
                    "SELECT id, link FROM fighters WHERE link = %s OR link = %s;",
                    (fighter_1, fighter_2)
                )
                id_map = {link: fid for fid, link in cur.fetchall()}
                fighter_a_id = id_map[fighter_1]
                fighter_b_id = id_map[fighter_2]
                fighter_a_id, fighter_b_id = sorted([fighter_a_id, fighter_b_id])

                # Step 3: Insert into matchups table
                insert_query = """
                    INSERT INTO matchups (fighter_a_id, fighter_b_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;  -- optional, prevents duplicate insert
                """
                cur.execute(insert_query, (fighter_a_id, fighter_b_id))

                #print("Inserted matchup between", names[0], "and", names[1])

    conn.close()

# Gets current opening odds from BestFightOdds if possible.  Will only get odds for fighters currently in the matchup table, odds cannot be scraped for not-upcoming fights and will have to be manually entered.
def update_odds():
    conn = get_db_connection()

    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT fighter_a_id, fighter_b_id FROM matchups;")
            rows = cur.fetchall()  # Returns a list of tuples
            for fighter_a_id, fighter_b_id in rows:
                cur.execute("""
                    SELECT id, name FROM fighters 
                    WHERE id IN (%s, %s);
                """, (fighter_a_id, fighter_b_id))
                names = {fid: name for fid, name in cur.fetchall()}

                fighter_a_name = names[fighter_a_id]
                fighter_b_name = names[fighter_b_id]
                print(f"({fighter_a_name}, {fighter_b_name})")

                date = datetime.now()
                odds = getFightOdds(fighter_a_name, fighter_b_name, date)
                if odds != None:
                    cur.execute("UPDATE fighters SET odds = %s WHERE id = %s;", (odds[0], fighter_a_id))
                    cur.execute("UPDATE fighters SET odds = %s WHERE id = %s;", (odds[1], fighter_b_id))
    conn.close()

def reset_fighter_data():
    conn = get_db_connection()
    cur = conn.cursor()

    delete_table_query = """
    DROP TABLE IF EXISTS fighters;
    """

    cur.execute(delete_table_query)
    conn.commit()
    cur.close()
    conn.close()

def get_matchups_content():
    conn = get_db_connection()
    cur = conn.cursor()

    get_matchups_query = """
    SELECT * FROM matchups;
    """

    cur.execute(get_matchups_query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


if __name__ == "__main__":
    conn = get_db_connection()
    cur = conn.cursor()
    
    if '--fresh' in sys.argv:
        reset_fighter_data()

    if '--debug' in sys.argv:
        matchups = get_matchups_content()
        print(matchups)

    create_table_query = """
    CREATE TABLE IF NOT EXISTS fighters (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        link TEXT UNIQUE,
        p4p_rank INTEGER,
        div_rank INTEGER,
        age INTEGER,
        height INTEGER,
        reach INTEGER,
        wins INTEGER,
        losses INTEGER,
        total_fights INTEGER,
        ranked_wins INTEGER,
        ranked_losses INTEGER,
        p4p_wins INTEGER,
        p4p_losses INTEGER,
        champion_wins INTEGER,
        champion_losses INTEGER,
        p4p_champion_wins INTEGER,
        p4p_champion_losses INTEGER,
        title_defenses INTEGER,
        title_losses INTEGER,
        win_rate DOUBLE PRECISION,
        ko_wins INTEGER,
        ko_losses INTEGER,
        ko_risk DOUBLE PRECISION,
        sub_wins INTEGER,
        sub_losses INTEGER,
        sub_risk DOUBLE PRECISION,
        finish_rate DOUBLE PRECISION,
        win_streak INTEGER,
        loss_streak INTEGER,
        last_five_fight_wins INTEGER,
        last_five_fight_losses INTEGER,
        last_five_fight_win_rate DOUBLE PRECISION,
        total_fight_time DOUBLE PRECISION,
        avg_fight_time DOUBLE PRECISION,
        SLpM DOUBLE PRECISION,
        SApM DOUBLE PRECISION,
        StrDef DOUBLE PRECISION,
        TDAvg DOUBLE PRECISION,
        TDAcc DOUBLE PRECISION,
        TDDef DOUBLE PRECISION,
        SubAvg DOUBLE PRECISION,
        total_head_strikes INTEGER,
        total_body_strikes INTEGER,
        total_leg_strikes INTEGER,
        total_strikes_landed INTEGER,
        total_strikes_missed INTEGER,
        StrAcc DOUBLE PRECISION,
        head_strikes_accuracy DOUBLE PRECISION,
        body_strikes_accuracy DOUBLE PRECISION,
        leg_strikes_accuracy DOUBLE PRECISION,
        rel_ko_rate DOUBLE PRECISION,
        abs_ko_rate DOUBLE PRECISION,
        rel_sub_rate DOUBLE PRECISION,
        abs_sub_rate DOUBLE PRECISION,
        SubAcc DOUBLE PRECISION,
        knockdowns INTEGER,
        knockdown_risk DOUBLE PRECISION,
        knockdown_durability DOUBLE PRECISION,
        win_finish_metric DOUBLE PRECISION,
        aggression_metric DOUBLE PRECISION,
        odds DOUBLE PRECISION,
        grappling_vs_striking DOUBLE PRECISION,
        AggDef_Delta DOUBLE PRECISION
    );

    CREATE TABLE IF NOT EXISTS matchups (
        id SERIAL PRIMARY KEY,
        fighter_a_id INTEGER,
        fighter_b_id INTEGER,
        fighter_a_prediction REAL,
        fighter_b_prediction REAL
    );

    ALTER TABLE matchups DROP CONSTRAINT IF EXISTS matchup_id_order;
    ALTER TABLE matchups DROP CONSTRAINT IF EXISTS unique_matchup_pair;

    ALTER TABLE matchups
    ADD CONSTRAINT matchup_id_order CHECK (fighter_a_id < fighter_b_id);

    ALTER TABLE matchups
    ADD CONSTRAINT unique_matchup_pair UNIQUE (fighter_a_id, fighter_b_id);
    """

    cur.execute(create_table_query)
    conn.commit()
    cur.close()
    conn.close()
    
    update_fighter_data()
    update_matchups(clean=True) # Refactoring idea: scan for change in matchups first instead of manually specifying clean.
    update_odds()
