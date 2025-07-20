import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from config import API_FOOTBALL_TOKEN, LIGAS_PERMITIDAS, FUNCIONES_PREMIUM
from database import db

class PremiumFeatures:
    def __init__(self):
        self.api_token = API_FOOTBALL_TOKEN
        self.headers = {'x-apisports-key': self.api_token}
        self.base_url = 'https://v3.football.api-sports.io'
    
    def get_advanced_stats(self, fixture_id: int) -> Dict:
        """Obtiene estadísticas avanzadas de un partido"""
        try:
            url = f"{self.base_url}/fixtures/statistics"
            params = {'fixture': fixture_id}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['response']:
                    stats = data['response']
                    advanced_stats = {}
                    
                    for team_stats in stats:
                        team_name = team_stats['team']['name']
                        team_stats_data = {}
                        
                        for stat in team_stats['statistics']:
                            stat_type = stat['type']
                            stat_value = stat['value']
                            team_stats_data[stat_type] = stat_value
                        
                        advanced_stats[team_name] = team_stats_data
                    
                    return advanced_stats
            return {}
        except Exception as e:
            logging.error(f"Error getting advanced stats: {e}")
            return {}
    
    def get_head_to_head(self, team1_id: int, team2_id: int, limit: int = 5) -> List[Dict]:
        """Obtiene historial de enfrentamientos entre dos equipos"""
        try:
            url = f"{self.base_url}/fixtures/headtohead"
            params = {
                'h2h': f"{team1_id}-{team2_id}",
                'last': limit
            }
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['response']:
                    h2h_matches = []
                    for match in data['response']:
                        h2h_matches.append({
                            'date': match['fixture']['date'],
                            'home_team': match['teams']['home']['name'],
                            'away_team': match['teams']['away']['name'],
                            'home_score': match['goals']['home'],
                            'away_score': match['goals']['away'],
                            'league': match['league']['name'],
                            'venue': match['fixture']['venue']['name'] if match['fixture']['venue'] else 'N/A'
                        })
                    return h2h_matches
            return []
        except Exception as e:
            logging.error(f"Error getting head to head: {e}")
            return []
    
    def get_team_form(self, team_id: int, last_matches: int = 5) -> Dict:
        """Obtiene la forma reciente de un equipo"""
        try:
            url = f"{self.base_url}/fixtures"
            params = {
                'team': team_id,
                'last': last_matches
            }
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['response']:
                    form_data = {
                        'matches': [],
                        'wins': 0,
                        'draws': 0,
                        'losses': 0,
                        'goals_for': 0,
                        'goals_against': 0
                    }
                    
                    for match in data['response']:
                        home_team = match['teams']['home']['name']
                        away_team = match['teams']['away']['name']
                        home_score = match['goals']['home']
                        away_score = match['goals']['away']
                        status = match['fixture']['status']['short']
                        
                        # Determinar resultado para el equipo
                        is_home = match['teams']['home']['id'] == team_id
                        team_score = home_score if is_home else away_score
                        opponent_score = away_score if is_home else home_score
                        
                        if status == 'FT':
                            if team_score > opponent_score:
                                form_data['wins'] += 1
                            elif team_score < opponent_score:
                                form_data['losses'] += 1
                            else:
                                form_data['draws'] += 1
                        
                        form_data['goals_for'] += team_score
                        form_data['goals_against'] += opponent_score
                        
                        form_data['matches'].append({
                            'home_team': home_team,
                            'away_team': away_team,
                            'score': f"{home_score}-{away_score}",
                            'status': status,
                            'team_score': team_score,
                            'opponent_score': opponent_score
                        })
                    
                    return form_data
            return {}
        except Exception as e:
            logging.error(f"Error getting team form: {e}")
            return {}
    
    def get_player_stats(self, player_id: int) -> Dict:
        """Obtiene estadísticas detalladas de un jugador"""
        try:
            url = f"{self.base_url}/players"
            params = {
                'id': player_id,
                'season': datetime.now().year
            }
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['response']:
                    player = data['response'][0]
                    stats = player['statistics'][0] if player['statistics'] else {}
                    
                    return {
                        'name': player['player']['name'],
                        'age': player['player']['age'],
                        'height': player['player']['height'],
                        'weight': player['player']['weight'],
                        'nationality': player['player']['nationality'],
                        'team': player['statistics'][0]['team']['name'] if player['statistics'] else 'N/A',
                        'league': player['statistics'][0]['league']['name'] if player['statistics'] else 'N/A',
                        'position': player['statistics'][0]['games']['position'] if player['statistics'] else 'N/A',
                        'games_played': stats.get('games', {}).get('appearences', 0),
                        'goals': stats.get('goals', {}).get('total', 0),
                        'assists': stats.get('goals', {}).get('assists', 0),
                        'yellow_cards': stats.get('cards', {}).get('yellow', 0),
                        'red_cards': stats.get('cards', {}).get('red', 0),
                        'minutes_played': stats.get('games', {}).get('minutes', 0)
                    }
            return {}
        except Exception as e:
            logging.error(f"Error getting player stats: {e}")
            return {}
    
    def get_league_standings_detailed(self, league_id: int) -> Dict:
        """Obtiene tabla de posiciones detallada con estadísticas"""
        try:
            url = f"{self.base_url}/standings"
            params = {
                'league': league_id,
                'season': datetime.now().year
            }
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['response']:
                    league_data = data['response'][0]
                    standings = []
                    
                    for team in league_data['league']['standings'][0]:
                        standings.append({
                            'position': team['rank'],
                            'team_name': team['team']['name'],
                            'team_logo': team['team']['logo'],
                            'points': team['points'],
                            'games_played': team['all']['played'],
                            'wins': team['all']['win'],
                            'draws': team['all']['draw'],
                            'losses': team['all']['lose'],
                            'goals_for': team['all']['goals']['for'],
                            'goals_against': team['all']['goals']['against'],
                            'goal_difference': team['goalsDiff'],
                            'form': team['form'],
                            'last_5': team['form'].split('')[-5:] if team['form'] else []
                        })
                    
                    return {
                        'league_name': league_data['league']['name'],
                        'league_logo': league_data['league']['logo'],
                        'season': league_data['league']['season'],
                        'standings': standings
                    }
            return {}
        except Exception as e:
            logging.error(f"Error getting detailed standings: {e}")
            return {}
    
    def get_weekly_summary(self, league_id: int) -> Dict:
        """Genera resumen semanal de una liga"""
        try:
            # Obtener partidos de la última semana
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            
            url = f"{self.base_url}/fixtures"
            params = {
                'league': league_id,
                'season': datetime.now().year,
                'from': start_date.isoformat(),
                'to': end_date.isoformat()
            }
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['response']:
                    summary = {
                        'league_name': LIGAS_PERMITIDAS.get(league_id, 'Unknown League'),
                        'period': f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}",
                        'total_matches': len(data['response']),
                        'matches': [],
                        'top_scorers': [],
                        'biggest_wins': [],
                        'goals_per_match': 0
                    }
                    
                    total_goals = 0
                    for match in data['response']:
                        home_team = match['teams']['home']['name']
                        away_team = match['teams']['away']['name']
                        home_score = match['goals']['home']
                        away_score = match['goals']['away']
                        status = match['fixture']['status']['short']
                        date = match['fixture']['date']
                        
                        if status == 'FT':
                            total_goals += home_score + away_score
                            goal_diff = abs(home_score - away_score)
                            
                            summary['matches'].append({
                                'home_team': home_team,
                                'away_team': away_team,
                                'score': f"{home_score}-{away_score}",
                                'date': date,
                                'goal_difference': goal_diff
                            })
                            
                            # Trackear mayores victorias
                            if goal_diff >= 3:
                                summary['biggest_wins'].append({
                                    'home_team': home_team,
                                    'away_team': away_team,
                                    'score': f"{home_score}-{away_score}",
                                    'goal_difference': goal_diff
                                })
                    
                    if summary['total_matches'] > 0:
                        summary['goals_per_match'] = round(total_goals / summary['total_matches'], 2)
                    
                    # Ordenar mayores victorias
                    summary['biggest_wins'] = sorted(summary['biggest_wins'], 
                                                   key=lambda x: x['goal_difference'], reverse=True)[:5]
                    
                    return summary
            return {}
        except Exception as e:
            logging.error(f"Error getting weekly summary: {e}")
            return {}
    
    def get_match_prediction(self, fixture_id: int) -> Dict:
        """Genera predicción básica para un partido"""
        try:
            # Obtener información del partido
            url = f"{self.base_url}/fixtures"
            params = {'id': fixture_id}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data['response']:
                    match = data['response'][0]
                    home_team_id = match['teams']['home']['id']
                    away_team_id = match['teams']['away']['id']
                    
                    # Obtener forma de ambos equipos
                    home_form = self.get_team_form(home_team_id)
                    away_form = self.get_team_form(away_team_id)
                    
                    # Obtener historial H2H
                    h2h = self.get_head_to_head(home_team_id, away_team_id)
                    
                    # Calcular predicción básica
                    prediction = {
                        'home_team': match['teams']['home']['name'],
                        'away_team': match['teams']['away']['name'],
                        'home_form': home_form,
                        'away_form': away_form,
                        'head_to_head': h2h,
                        'prediction': self._calculate_prediction(home_form, away_form, h2h)
                    }
                    
                    return prediction
            return {}
        except Exception as e:
            logging.error(f"Error getting match prediction: {e}")
            return {}
    
    def _calculate_prediction(self, home_form: Dict, away_form: Dict, h2h: List) -> Dict:
        """Calcula predicción basada en forma y H2H"""
        try:
            # Puntos de forma
            home_points = home_form.get('wins', 0) * 3 + home_form.get('draws', 0)
            away_points = away_form.get('wins', 0) * 3 + away_form.get('draws', 0)
            
            # Ventaja local (30% más puntos)
            home_points = int(home_points * 1.3)
            
            # Análisis H2H
            h2h_home_wins = 0
            h2h_away_wins = 0
            h2h_draws = 0
            
            for match in h2h:
                if match['home_score'] > match['away_score']:
                    h2h_home_wins += 1
                elif match['away_score'] > match['home_score']:
                    h2h_away_wins += 1
                else:
                    h2h_draws += 1
            
            # Calcular probabilidades
            total_points = home_points + away_points
            if total_points > 0:
                home_prob = round((home_points / total_points) * 100, 1)
                away_prob = round((away_points / total_points) * 100, 1)
                draw_prob = round(100 - home_prob - away_prob, 1)
            else:
                home_prob = away_prob = draw_prob = 33.3
            
            # Ajustar por H2H
            if h2h:
                h2h_total = len(h2h)
                h2h_home_advantage = (h2h_home_wins / h2h_total) * 10
                h2h_away_advantage = (h2h_away_wins / h2h_total) * 10
                
                home_prob += h2h_home_advantage
                away_prob += h2h_away_advantage
                draw_prob = max(0, 100 - home_prob - away_prob)
            
            return {
                'home_win_probability': round(home_prob, 1),
                'away_win_probability': round(away_prob, 1),
                'draw_probability': round(draw_prob, 1),
                'predicted_result': self._get_predicted_result(home_prob, away_prob, draw_prob),
                'confidence': self._get_confidence_level(home_prob, away_prob, draw_prob)
            }
        except Exception as e:
            logging.error(f"Error calculating prediction: {e}")
            return {}
    
    def _get_predicted_result(self, home_prob: float, away_prob: float, draw_prob: float) -> str:
        """Obtiene el resultado predicho"""
        max_prob = max(home_prob, away_prob, draw_prob)
        if max_prob == home_prob:
            return "Victoria Local"
        elif max_prob == away_prob:
            return "Victoria Visitante"
        else:
            return "Empate"
    
    def _get_confidence_level(self, home_prob: float, away_prob: float, draw_prob: float) -> str:
        """Obtiene el nivel de confianza de la predicción"""
        max_prob = max(home_prob, away_prob, draw_prob)
        if max_prob >= 60:
            return "Alta"
        elif max_prob >= 45:
            return "Media"
        else:
            return "Baja"

# Instancia global de funciones premium
premium = PremiumFeatures() 