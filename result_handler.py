import redis


def handle_result(player_id, r, result):
    guessed = f"Угадано {player_id}"
    unguessed = f"Не угадано {player_id}"
    guessed_score = r.get(guessed)
    unguessed_score = r.get(unguessed)
    if result:
        if guessed_score:
            r.set(guessed, str(int(guessed_score) + 1))
        else:
            r.set(guessed, "1")
    else:
        if unguessed_score:
            r.set(unguessed, str(int(unguessed_score) + 1))
        else:
            r.set(unguessed, "1")
    last_question = r.get(player_id)
    r.delete(last_question)
    r.delete(player_id)
