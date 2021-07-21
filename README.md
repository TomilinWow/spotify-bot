# spotify-bot
Чатбот Spotify с использованием Rasa

# Чтобы запустить чат-бот необходимо:
1) Получить свой refresh token и base64 Spotify, подробнее по ссылке https://developer.spotify.com/documentation/general/guides/authorization-guide/
2) Полученные refresh token и base64 вбить в файл spotify_token, вместо '':                                                               
self.refresh_token = ''                                                            
self.base_64 = ''

3) pip install rasa
4) cd folder project
5) rasa run actions + rasa shell

# Примеры работы чат-бота:
•	Your input ->  можешь включи трек Алиса                             
Наслаждайся музыкой!

•	Your input ->  включи плейлист хиты лета                                  
Держи!

•	Your input ->  добавь песню в избранное                                     
Добавлена!!!

•	Your input ->  сохрани текущую песню                              
Добавлена!!!

•	Your input ->  включи летние песни                                          
Держи!
