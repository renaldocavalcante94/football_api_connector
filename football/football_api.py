from requests.api import head
from football.api_base import BaseAPI
from .api_base import *
import pandas as pd
from dataclasses import dataclass


class FootballAPI(BaseAPI):
    base_url = "https://v3.football.api-sports.io/"

    def __init__(self,rapidapi_key,rapidapi_host):
        super().__init__(rapidapi_key, rapidapi_host)

    def list_timezones(self):
        url = self.base_url + "timezone"
        headers = self.base_headers
        params = None

        response = self.get(url,headers,params)

        return response.json()["response"]

    def set_timezone(self,timezone):
        timezones = self.list_timezones()["timezone"]

        if timezone not in timezones:
            raise ValueError(f"{timezone} doesn't exists in this API please use the method list_timezones to see the possible timezones")
        else:
            self.timezone = timezone
            return True

    def list_countries(self,result_type="full"):
        """List all countries availables in the Football-API

        Args:
            result_type (str, optional): [description]. Defaults to "full" , 
                if full the response object will return all 3 attributes , country, code and flag. 
                If result_type == "basic" will return only the country 
                If result_type == "with-flag" will return country and the flag attribute
                if result_type == "with-code" will return country and the code attribute


        Returns:
            list: list of all countrys based on the result_type 
        """

        url = self.base_url + "countries"
        headers = self.base_headers
        params = None

        response = self.get(url,headers,params)

        response = response.json()["response"]

        if result_type == "full":
            response = response
        elif result_type == "basic":
            keep_columns = ["country"]
            response = pd.DataFrame(response)[keep_columns].to_dict("records")
        elif result_type == "with-flag":
            keep_columns = ["country","flag"]
            response = pd.DataFrame(response)[keep_columns].to_dict("records")
        elif result_type == "with-code":
            keep_columns = ["country","code"]
            response = pd.DataFrame(response)[keep_columns].to_dict("records")

        return response

    def _get_all_leagues(self):
        url = self.base_url + "leagues"
        headers = self.base_headers
        params = None

        response =self.get(url,headers,params).json()

        return response

    def list_leagues(self):

        leagues = []

        leagues_objects = self._get_all_leagues()["response"]

        for league_object in leagues_objects:
            leagues.append(league_object["league"])

        return leagues

    def all_lives_fixtures(self):
        url = self.base_url + "fixtures"

        params = {"live": "all"}

        response = self.get(url,self.base_headers,params).json()["response"]
        print(len(response))

        live_fixtures = []

        for i,fixture in enumerate(response):
            new_fixture = Fixture(self,fixture["fixture"]["id"])

            live_fixtures.append(new_fixture)

        return live_fixtures



class Country(FootballAPI):
    
    def __init__(self, football_api,name,object_params=None):

        super().__init__(football_api.api_key, football_api.api_host)
        self.url = self.base_url + "countries"

        if object_params == None:
            request_response = self._get_country_by_name(name)
            self.name = request_response["name"]
            self.code = request_response["code"]
            self.flag_url = request_response["flag"]
        else: 
            self.name = object_params["name"]
            self.code = object_params["code"]
            self.flag_url = object_params["flag"]

    def __str__(self):
        return f"country: {self.name}, code: {self.code}"

    def _get_country_by_name(self,name):
        params = {"name": name}
        response = self.get(self.url,self.base_headers,params).json()
        results = response["results"]

        try:

            if results == 0:
                raise RequestException(f"{name} isn't a valid country name")
            elif results == 1 : 
                return response["response"][0]
            else: 
                raise AttributeError(f"{name} must return only one country")
        
        except Exception as error:
            print(response)
            raise error

class Team(FootballAPI):
    
    id = int(),
    name = str(),
    logo_url = str(),

    def __init__(self, football_api):
        super().__init__(football_api.api_key, football_api.api_host)
        self.url = self.base_url + "teams"

    def __str__(self):
        return f"id: {self.id}, name:{self.name}, logo_url:{self.logo_url}"
    
    def __repr__(self):
        return f"Team(id={self.id},name={self.name},logo_url={self.logo_url})"

class League(FootballAPI):


    def __init__(self, football_api, id=None):
        self.football_api = football_api
        super().__init__(football_api.api_key, football_api.api_host)
        self.url = self.base_url + "leagues"
        
        self.id = id
        league_object = self._get_league_by_id()
        
        self.name = league_object["league"]["name"]
        self.type = league_object["league"]["type"]
        self.logo_url = league_object["league"]["logo"]

        self.country = Country(football_api,name=league_object["country"]["name"],object_params=league_object["country"])

    def __str__(self):
        return f"League: {self.name}, Id: {self.id}, Type: {self.type}, Country: {self.country.name}"

    def __repr__(self):
        return f"League(id={self.id}, name={self.name}, type={self.type}, logo={self.logo_url}, country={self.country.name}"

    def _get_league_by_id(self):
        params = {"id": self.id}

        response = self.get(self.url,self.base_headers,params).json()

        if len(response["response"]) > 1:
            raise KeyError(f"This {self.id} return more than one league , please check")
        
        league = response["response"][0]

        return league

    def _process_seasons(self,seasons):

        for i,season in enumerate(seasons):
            del season["coverage"]
            seasons[i] = season

        return seasons

    def get_standing(self,season):
        seasons_df = pd.DataFrame(self.seasons)

        if season not in seasons_df["year"].values:
            raise ValueError(f"Season: {season} isnt a valid season for this league")

        url = self.base_url + "standings"
        params = {"league": self.id, "season": season}

        response = self.get(url,self.base_headers,params)

        standing_object = response.json()

        return standing_object

    def live_fixtures(self,timezone=None):
        url = self.base_url + "fixtures"

        params = {"live": "all", "timezone": timezone, "league": self.id}

        response = self.get(url,self.base_headers,params).json()["response"]
        print(len(response))

        live_fixtures = []

        for i,fixture in enumerate(response):
            new_fixture = Fixture(self.football_api,fixture["fixture"]["id"])

            live_fixtures.append(new_fixture)

        self.live_fixtures = live_fixtures
        
        return live_fixtures

class Fixture(FootballAPI):

    timezone = "America/Sao_Paulo"

    def __init__(self, football_api,id):
        self.football_api = football_api
        super().__init__(football_api.api_key, football_api.api_host)

        self.url = self.base_url + "fixtures"
        
        self.id = id

        self._set_class_attributes_()


    def _get_fixture_by_id(self):
        params = {"timezone": self.timezone, "id": self.id}

        response = self.get(self.url,self.base_headers,params).json()["response"][0]

        return response

    def _set_class_attributes_(self):
        
        response = self._get_fixture_by_id()

        fixture_infos = response["fixture"]
        league_infos = response["league"]
        teams_infos = response["teams"]
        goals_infos = response["goals"]
        events_infos = response["events"]

        statistics_infos = response["statistics"]

        self.referee = fixture_infos['referee']
        self.date = fixture_infos["date"]
        self.timestamp = fixture_infos["timestamp"]
        self.periods = fixture_infos["periods"], 
        self.venue = fixture_infos["venue"],
        self.status = fixture_infos["status"]
        self.league = League(self.football_api,id=league_infos["id"])
        home_team_object = teams_infos["home"]
        home_team_object["goals"] = goals_infos["home"]
        away_team_object = teams_infos["away"]
        away_team_object["goals"] = goals_infos["away"]
        statistics_tuple = self._procecess_statistics(statistics_infos,home_team_object,away_team_object)
        home_statistics_object = statistics_tuple[0]
        away_statistics_object = statistics_tuple[1]
        self.home_team = TeamInFixture(home_team_object,home_statistics_object)
        self.away_team = TeamInFixture(away_team_object,away_statistics_object)




    def _procecess_statistics(self,statistics_infos,home_team_object,away_team_object):

        for statistics_info in statistics_infos:
            
            team_id = statistics_info["team"]["id"]

            statistics = statistics_info["statistics"]

            statistic_object = {}

            for statistic in statistics:
                statistic_object[statistic["type"]] = statistic["value"]
            
            if team_id == home_team_object["id"]:
                home_team_statistics = statistic_object
            else:
                away_team_statistics = statistic_object

        return home_team_statistics,away_team_statistics        


    def __str__(self):
        return f"""Fixture -> Id: {self.id}, Referee: {self.referee}, Date: {self.date}, Periods: {self.periods} 
League -> {self.league} 
Venue -> {self.venue} 
Status-> {self.status}
Home Team -> {self.home_team}
Home Team Statistics -> {self.home_team.statistics}
Away Team -> {self.away_team}
Away Team Statistics -> {self.away_team.statistics}"""

    def __repr__(self):
        return f"""Fixture(id={self.id}, date={self.date}, periods={self.periods}, league_name={self.league.name}, country={self.league.country.name})"""



class TeamInFixture:

    def __init__(self,construct_object,statistics_object):
        self.id = construct_object["id"]
        self.name = construct_object["name"]
        self.logo_url = construct_object["logo"]
        self.winner = construct_object["winner"]
        self.goals = construct_object["goals"]
        self.statistics = TeamFixtureStatistics(statistics_object)

    def __str__(self):
        return f"id:{self.id}, name:{self.name}, goals:{self.goals}, winner:{self.winner}"
    
    def __repr__(self):
        return f"Team(id={self.id},name={self.name},logo_url={self.logo_url},winner={self.winner})"

class TeamFixtureStatistics:

    def __init__(self,construct_object):
        self.total_shots = construct_object["Total Shots"]
        self.shots_on_goal = construct_object["Shots on Goal"]
        self.shots_off_goal = construct_object["Shots off Goal"]
        self.blocked_shots = construct_object["Total Shots"]
        self.shots_insidebox = construct_object["Shots insidebox"]
        self.shots_outsidebox = construct_object["Shots outsidebox"]
        self.fouls = construct_object["Fouls"]
        self.corner_kicks = construct_object["Corner Kicks"]
        self.offsides = construct_object["Offsides"]
        self.ball_possession = construct_object["Ball Possession"]
        self.yellow_cards = construct_object["Yellow Cards"]
        self.red_cards = construct_object["Red Cards"]
        self.goalkeeper_saves = construct_object["Goalkeeper Saves"]
        self.total_passes = construct_object["Total passes"]
        self.passes_accurate = construct_object["Passes accurate"]
        self.passes_percentage = construct_object["Passes %"]


    def __str__(self):
        return f"TotalShots: {self.total_shots}, ShotsOnGoal: {self.shots_on_goal}, ShotsOffGoal: {self.shots_off_goal}, BlockedShots: {self.blocked_shots}, ShotsInsideBox: {self.shots_insidebox},ShotsOffsideBox: {self.shots_outsidebox}, Fouls: {self.fouls}, ConerKicks: {self.corner_kicks}, OffSides: {self.offsides}, BallPossession: {self.ball_possession}, YellowCards: {self.yellow_cards},RedCards: {self.red_cards}, GoalkeeperSaves: {self.goalkeeper_saves}, TotalPasses: {self.total_passes}, PassesAccurate: {self.passes_accurate}, PassesPercentage: {self.passes_percentage}"

    def __repr__(self):
        return f"TeamFixtureStatistics(total_shots={self.total_shots},shots_on_goal={self.shots_on_goal},shots_off_goal={self.shots_off_goal},blocked_shots={self.blocked_shots},shots_insidebox={self.shots_insidebox},shots_outsidebox={self.shots_outsidebox},fouls={self.fouls},corner_kicks={self.corner_kicks},offsides={self.offsides},ball_possession={self.ball_possession},yellow_cards={self.yellow_cards},red_cards={self.red_cards},goalkeeper_saves={self.goalkeeper_saves},total_passes={self.total_passes},passes_accurate={self.passes_accurate},passes_percentage={self.passes_percentage})"



