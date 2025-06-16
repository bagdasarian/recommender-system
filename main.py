import tkinter as tk
from gui import create_app_state, load_data, setup_gui
import pandas as pd

def run_app():
    """Запускает приложение рекомендаций фильмов"""
    movies = pd.read_csv('data/movies.csv')
    ratings = pd.read_csv('data/ratings.csv')
    merged_data = pd.merge(ratings, movies[['movieId', 'title']], on='movieId')
    
    # Инициализация приложения 
    app_state = create_app_state()
    load_data(app_state, merged_data)
    setup_gui(app_state)
    app_state['root'].mainloop()

if __name__ == "__main__":
    run_app()