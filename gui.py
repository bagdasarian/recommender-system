import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from recommender import calculate_movie_stats, average_recommend_for_user, create_user_movie_matrix, calculate_movie_popularity, collaborative_recommend_for_user
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def create_app_state():
    #Создает состояние приложения
    return {
        'data': pd.DataFrame(),
        'movie_stats': None,
        'user_movie_matrix': None,
        'movie_popularity': None,
        'root': None,
        'user_id_entry': None,
        'recommender_type': None,
        'tree': None,
        'notebook': None,
        'canvas': None,
        'last_recommendations': None,
        'last_score_column': None,
        'plot_frame': None  
    }

def load_data(app_state, data):
    #Загружает данные и инициализирует структуры для рекомендаций
    app_state['data'] = data
    app_state['movie_stats'] = calculate_movie_stats(data)
    app_state['user_movie_matrix'] = create_user_movie_matrix(data)
    app_state['movie_popularity'] = calculate_movie_popularity(data)

def plot_recommendations(app_state):
    #Строит график рекомендаций
    if app_state['last_recommendations'] is None or app_state['last_recommendations'].empty:
        messagebox.showinfo("Информация", "Сначала получите рекомендации")
        return

    # Создание фигуры matplotlib
    fig, ax = plt.subplots(figsize=(8, 5))
    titles = app_state['last_recommendations']['title']
    scores = app_state['last_recommendations'][app_state['last_score_column']]

    # Столбчатая диаграмма
    bars = ax.bar(titles, scores, color='#1f77b4')

    # Подписи к осям и заголовок
    ax.set_title("Рейтинги рекомендуемых фильмов")
    ax.set_xlabel("Фильмы")
    ax.set_ylabel("Рейтинг" if app_state['last_score_column'] == "rating" else "Оценка")

    # Поворот названий фильмов для лучшей читаемости
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.3, top=0.9, left=0.1, right=0.9)

    # Установка диапазона по оси Y, чтобы усилить визуальные различия
    score_min = scores.min()
    score_max = scores.max()
    y_range = score_max - score_min
    ax.set_ylim(score_min - y_range * 0.2, score_max + y_range * 0.2)  # Растягиваем шкалу

    # Добавляем горизонтальную сетку
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)

    # Подписываем каждый столбец его значением
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 точки выше текста
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

    # Удаление предыдущего canvas, если он существует
    if app_state['canvas'] is not None:
        app_state['canvas'].get_tk_widget().destroy()

    # Встраивание графика в tkinter
    app_state['canvas'] = FigureCanvasTkAgg(fig, master=app_state['plot_frame'])
    app_state['canvas'].draw()
    app_state['canvas'].get_tk_widget().pack(fill='both', expand=True)

def get_recommendations(app_state):
    """Получает рекомендации для пользователя"""
    try:
        user_id = int(app_state['user_id_entry'].get())
        recommender_type = app_state['recommender_type'].get()
        
        # Очистка таблицы
        for item in app_state['tree'].get_children():
            app_state['tree'].delete(item)
        
        # Получение рекомендаций
        if recommender_type == "average":
            recommendations = average_recommend_for_user(
                app_state['data'], app_state['movie_stats'], user_id
            )
            score_column = "rating"
        else:
            recommendations = collaborative_recommend_for_user(
                app_state['data'], app_state['user_movie_matrix'], 
                app_state['movie_popularity'], user_id
            )
            score_column = "score"
        
        # Сохранение рекомендаций для графика
        app_state['last_recommendations'] = recommendations
        app_state['last_score_column'] = score_column
        
        # Отображение результатов в таблице
        for _, row in recommendations.iterrows():
            app_state['tree'].insert("", tk.END, values=(row["title"], f"{row[score_column]:.2f}"))
            
    except ValueError:
        messagebox.showerror("Ошибка", "Пожалуйста, введите корректный ID пользователя (целое число)")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")

def setup_gui(app_state):
    #Настраивает графический интерфейс
    app_state['root'] = tk.Tk()
    app_state['root'].title("Система рекомендаций фильмов")
    
    # Настройка корневого окна для масштабирования
    app_state['root'].grid_rowconfigure(1, weight=1)
    app_state['root'].grid_columnconfigure(0, weight=1)
    
    # Контейнер для верхней части (ввод и кнопки)
    top_frame = tk.Frame(app_state['root'])
    top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
    top_frame.grid_columnconfigure(1, weight=1)
    
    # Поле ввода ID пользователя
    tk.Label(top_frame, text="Введите ID пользователя:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    app_state['user_id_entry'] = tk.Entry(top_frame)
    app_state['user_id_entry'].grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    
    # Выбор типа рекомендаций
    tk.Label(top_frame, text="Тип рекомендаций:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    app_state['recommender_type'] = tk.StringVar(value="average")
    tk.Radiobutton(top_frame, text="На основе среднего", variable=app_state['recommender_type'], 
                  value="average").grid(row=1, column=1, padx=5, pady=5, sticky="w")
    tk.Radiobutton(top_frame, text="Коллаборативная", variable=app_state['recommender_type'], 
                  value="collaborative").grid(row=1, column=2, padx=5, pady=5, sticky="w")
    
    # Кнопки
    button_frame = tk.Frame(top_frame)
    button_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="ew")
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)
    
    tk.Button(button_frame, text="Получить рекомендации", 
             command=lambda: get_recommendations(app_state)).grid(row=0, column=0, padx=5, sticky="ew")
    tk.Button(button_frame, text="Показать график", 
             command=lambda: plot_recommendations(app_state)).grid(row=0, column=1, padx=5, sticky="ew")
    
    # Вкладки для таблицы и графика
    app_state['notebook'] = ttk.Notebook(app_state['root'])
    app_state['notebook'].grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
    
    # Вкладка для таблицы
    table_frame = tk.Frame(app_state['notebook'])
    app_state['notebook'].add(table_frame, text="Таблица")
    
    app_state['tree'] = ttk.Treeview(table_frame, columns=("Title", "Score"), show="headings")
    app_state['tree'].heading("Title", text="Название фильма")
    app_state['tree'].heading("Score", text="Оценка")
    app_state['tree'].pack(fill="both", expand=True, padx=10, pady=5)
    
    # Настройка размеров столбцов
    app_state['tree'].column("Title", width=300, stretch=True)
    app_state['tree'].column("Score", width=100, stretch=True)
    
    # Полоса прокрутки для таблицы
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=app_state['tree'].yview)
    scrollbar.pack(side="right", fill="y")
    app_state['tree'].configure(yscrollcommand=scrollbar.set)
    
    # Вкладка для графика
    app_state['plot_frame'] = tk.Frame(app_state['notebook'])
    app_state['notebook'].add(app_state['plot_frame'], text="График")