# Hangman Game API

#### Created by: John Laine

### [Live Demo](https://apis-explorer.appspot.com/apis-explorer/?base=https://named-magnet-141501.appspot.com/_ah/api#p/hangman/v1.0/)

## Project Description
An API with endpoints that will allow others to develop a front-end for the game.
This project was created and submitted to Udacity as part of the 'Full Stack Web Developer' Nanodegree

## Game Description
Hangman is a guessing game where a player is given a certain number of 'misses' to guess a secret word. Each time the player guesses a letter or the secret word incorrectly, they lose one of thier 'misses'

## How To Play The game
1. Creat a user `create_user`, user_name is required, email is not.
2. Create a game `create_game`, user_name is required, you can select the number of 'misses' allowed also if you like. The `urlsafe_game_key` will allow you to retrieve the game.
A random word will be chosen as the 'Secret Word' you will need to guess.
3. At this point, you can either guess a letter `guess_letter` or try to guess the secret word `guess_word`.
4. If you run out of 'misses', you have lost and the game is over.
5. If you guess all the letters `guess_letter` or guess the whole word `guess_word` you have won and the game is over.
6. You may cancel a game with `cancel_game`

## Score Keeping
The scoring is as follows:

- 10 points:
    If a letter is guessed correctly.
- 20 points:
    If a word is guessed correctly
- 20 points:
    For each unguessed letter remaining in the word when the word is correctly guessed.

So if the secret word was 'HOUSE' and you had already guessed the 'H' and 'S', you would have 20 points (10 for each letter). If you then decided to guess the secret word and you did so correctly you would get an additional 80 points (20 for guessing the word and 60 for the 3 unguessed letters remaining)

## Endpoints

- **create_user:**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name(required), email(optional)
    - Returns: Message confirming creation of the user.
    - Raises: ConflictException - if the user_name already exists.
    - Description: Creates a new user.
    - URL: https://named-magnet-141501.appspot.com/_ah/api/hangman/v1.0/users
- **get_user_games:**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: A list of GameForms that contain current game state for each game created by user.
    - Raises: NotFoundException - if user does not exist.
    - Description: Returns all games created by a user.
- **get_user_scores:**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: A list of ScoreForms that contain score information for each game a user has completed.
    - Raises: NotFoundException - if user does not exist.
    - Description: Returns all scores for a user.
- **get_user_rankings:**
    - Path: 'user/ranking'
    - Method: GET
    - Parameters: None
    - Returns: RankingForms
    - Raises: None
    - Description: Returns a list of users with the highest scores.
- **create_game:**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, misses_allowed(optional, default=5)
    - Returns: GameForm with initial game state.
    - Raises: NotFoundException - if user_name does not exist.
    - Description: Creates a new game.
- **get_game:**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with game state
    - Raises: NotFoundException - if urlsafe_game_key does not exists
    - Description: Returns a game state
- **guess_letter:**
    - Path: 'game/{urlsafe_game_key}/guess/letter'
    - Method: PUT
    - Parameters: urlsafe_game_key, letter_guess
    - Returns: GameForm with updated game state.
    - Raises: BadRequestException - if game is over or cancelled or more than one letter was submitted.
    - Description: Allows player to guess a letter.
- **guess_word:**
    - Path: 'game/{urlsafe_game_key}/guess/word'
    - Method: PUT
    - Parameters: urlsafe_game_key, word_guess
    - Returns: GameForm with updated game state.
    - Raises: BadRequestException - if game is over or cancelled.
    - Description: Allows player to guess the word.
- **get_game_history:**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameHistoryForm for each history element
    - Raises: None
    - Description: Get the history of a game.
- **cancel_game:**
    - Path: 'game/{urlsafe_game_key}/cancel'
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: GameForm with updated game state.
    - Raises: - NotFoundException - if the game does not exist. BadRequestException - if the game is already over or cancelled.
    - Description: Cancels a game.
- **get_scores:**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: A list of ScoreForms
    - Raises: None
    - Description: Returns all scores for all completed games.
- **get_high_scores:**
    - Path: 'scores/high'
    - Method: GET
    - Parameters: number_of_results(optional, default-all)
    - Returns: A list of ScoreForms
    - Raises: None
    - Description: Returns a list of high scores
