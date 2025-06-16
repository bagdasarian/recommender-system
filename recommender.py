import pandas as pd


def calculate_movie_stats(data):
    # Рассчитывает средний рейтинг и количество оценок для каждого фильма
    stats = data.groupby('movieId')['rating'].agg(['mean', 'count'])
    stats.columns = ['avg_rating', 'rating_count']
    return stats.reset_index()


def average_recommend_for_user(
        data, movie_stats, user_id, top_n=10, min_ratings=50):
    # Рекомендации на основе среднего рейтинга
    # Фильмы, которые пользователь уже смотрел
    watched = data[data['userId'] == user_id]['movieId'].unique()
    
    # Фильмы с достаточным количеством оценок
    popular_movies = movie_stats[movie_stats['rating_count'] >= min_ratings]
    
    # Рекомендации (исключая просмотренные)
    recommendations = (
        popular_movies[~popular_movies['movieId'].isin(watched)]
        .sort_values(['avg_rating', 'rating_count'], ascending=[False, False])
        .head(top_n)
        .merge(data[['movieId', 'title']].drop_duplicates(), on='movieId')
    )
    
    return recommendations[['title', 'avg_rating']].rename(
        columns={'avg_rating': 'rating'})


def create_user_movie_matrix(data):
    # Создает матрицу пользователь-фильм
    return data.pivot_table(
        index='userId', columns='movieId', values='rating', fill_value=0)


def calculate_movie_popularity(data):
    # Рассчитывает количество оценок для каждого фильма
    return data.groupby('movieId')['rating'].count()


def collaborative_recommend_for_user(
        data, user_movie_matrix, movie_popularity, user_id,
        top_n=10, min_ratings=50):
    # Улучшенный коллаборативный метод с коррекцией оценок
    if user_id not in user_movie_matrix.index:
        return pd.DataFrame(columns=['title', 'score'])

    # Предварительные расчёты: средние рейтинги пользователей и фильмов + глобальный средний рейтинг
    user_avg = data.groupby('userId')['rating'].mean()
    movie_avg = data.groupby('movieId')['rating'].mean()
    global_avg = data['rating'].mean()

    # Получаем оценки целевого пользователя
    target_ratings = user_movie_matrix.loc[user_id]

    # Вычисляем схожесть с другими пользователями (учитываем только положительные корреляции)
    similarity = user_movie_matrix.corrwith(
        pd.Series(target_ratings),
        axis=1,
        method='pearson'
    ).dropna()

    # Удаляем отрицательные корреляции и текущего пользователя
    similarity = similarity[similarity > 0].drop(index=user_id, errors='ignore')
    if similarity.empty:
        return pd.DataFrame(columns=['title', 'score'])

    # Нормализуем коэффициенты схожести (приводим к диапазону [0.5, 1])
    similarity = (
        (similarity - similarity.min()) /
        (similarity.max() - similarity.min()) * 0.5 + 0.5
    )

    # Берем топ-20 похожих пользователей для устойчивости
    similar_users = similarity.nlargest(20)

    # Собираем оценки похожих пользователей
    recommendations = pd.DataFrame(columns=['score'])

    for movie_id in user_movie_matrix.columns:
        # Оценки похожих пользователей для текущего фильма
        movie_ratings = user_movie_matrix.loc[similar_users.index, movie_id]
        movie_ratings = movie_ratings[movie_ratings > 0]

        if len(movie_ratings) == 0:
            continue

        # Взвешенная оценка с учетом схожести
        weighted_sum = (movie_ratings * similar_users[movie_ratings.index]).sum()
        weight_sum = similar_users[movie_ratings.index].sum()
        predicted_rating = weighted_sum / weight_sum

        # Добавляем "базовый уровень" (усреднение между пользовательским, фильмовым и глобальным рейтингом)
        base_rating = (
            user_avg.loc[user_id] + movie_avg.loc[movie_id] + global_avg) / 3
        predicted_rating = (predicted_rating + base_rating) / 2  # Смешивание

        # Мягкая коррекция (+5%, не выше 5.0)
        predicted_rating = min(predicted_rating * 1.05, 5.0)

        recommendations.loc[movie_id, 'score'] = predicted_rating

    # Удаляем уже просмотренные фильмы
    already_seen = target_ratings[target_ratings > 0].index
    recommendations = recommendations.drop(
        index=already_seen, errors='ignore')

    # Фильтруем по популярности
    popular_movies = movie_popularity[movie_popularity >= min_ratings].index
    recommendations = recommendations[recommendations.index.isin(popular_movies)]

    # Добавляем movieId как столбец
    recommendations = recommendations.reset_index()
    recommendations.columns = ['movieId', 'score']

    # Добавляем названия фильмов
    recommendations = (
        recommendations
        .merge(data[['movieId', 'title']].drop_duplicates(), on='movieId')
        .sort_values('score', ascending=False)
        .head(top_n)
    )

    return recommendations[['title', 'score']]