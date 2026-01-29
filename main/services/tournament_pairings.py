from typing import List, Tuple
import random

def has_played_against(tournament, player1, player2):
    """Check if two players have already faced each other in this tournament"""
    print(f"Checking if {player1.get_display_name()} has played against {player2.get_display_name()}")
    has_played = tournament.matches.filter(
        white_player__in=[player1, player2],
        black_player__in=[player1, player2]
    ).exists()
    print(f"Result: {'Yes' if has_played else 'No'}")
    return has_played

def get_color_counts(tournament, player):
    """Get the number of times a player had white and black pieces"""
    white_count = tournament.matches.filter(white_player=player, black_player__isnull=False).count()
    black_count = tournament.matches.filter(black_player=player).count()
    print(f"Color counts for {player.get_display_name()}: White={white_count}, Black={black_count}")
    return white_count, black_count

def get_recent_color_history(tournament, player, rounds_to_check=2):
    """Get the color history for a player in the most recent rounds.
    Returns a list of colors ('white', 'black', or None for bye) from most recent to oldest.
    """
    # Get all matches where player participated, ordered by round (most recent first)
    matches = tournament.matches.filter(
        round_number__lte=tournament.current_round
    ).filter(
        white_player=player
    ) | tournament.matches.filter(
        round_number__lte=tournament.current_round
    ).filter(
        black_player=player
    )
    
    matches = matches.order_by('-round_number')[:rounds_to_check]
    
    colors = []
    for match in matches:
        if match.black_player is None:
            colors.append(None)  # Bye
        elif match.white_player == player:
            colors.append('white')
        else:
            colors.append('black')
    
    return colors

def assign_colors_round_robin(player1, player2, tournament):
    """Assign colors ensuring no player plays the same color more than twice consecutively.
    This follows the official rule: no more than 2 consecutive rounds with the same color.
    """
    p1_history = get_recent_color_history(tournament, player1, rounds_to_check=2)
    p2_history = get_recent_color_history(tournament, player2, rounds_to_check=2)
    
    # Check if player1 has played the same color twice in a row
    p1_needs_switch = False
    if len(p1_history) >= 2 and p1_history[0] == p1_history[1] and p1_history[0] is not None:
        p1_needs_switch = True
        required_color_p1 = 'black' if p1_history[0] == 'white' else 'white'
    elif len(p1_history) >= 1 and p1_history[0] is not None:
        # Prefer switching color if possible
        preferred_color_p1 = 'black' if p1_history[0] == 'white' else 'white'
    else:
        preferred_color_p1 = None
    
    # Check if player2 has played the same color twice in a row
    p2_needs_switch = False
    if len(p2_history) >= 2 and p2_history[0] == p2_history[1] and p2_history[0] is not None:
        p2_needs_switch = True
        required_color_p2 = 'black' if p2_history[0] == 'white' else 'white'
    elif len(p2_history) >= 1 and p2_history[0] is not None:
        # Prefer switching color if possible
        preferred_color_p2 = 'black' if p2_history[0] == 'white' else 'white'
    else:
        preferred_color_p2 = None
    
    # Priority 1: If one player MUST switch (has played same color twice), assign accordingly
    if p1_needs_switch:
        if required_color_p1 == 'white':
            print(f"Assigning white to {player1.get_display_name()} (must switch from {p1_history[0]})")
            return player1, player2
        else:
            print(f"Assigning white to {player2.get_display_name()} (player1 must switch from {p1_history[0]})")
            return player2, player1
    
    if p2_needs_switch:
        if required_color_p2 == 'white':
            print(f"Assigning white to {player2.get_display_name()} (must switch from {p2_history[0]})")
            return player2, player1
        else:
            print(f"Assigning white to {player1.get_display_name()} (player2 must switch from {p2_history[0]})")
            return player1, player2
    
    # Priority 2: If both have preferences, try to satisfy both
    if preferred_color_p1 == 'white' and preferred_color_p2 == 'black':
        print(f"Assigning white to {player1.get_display_name()} (both players prefer different colors)")
        return player1, player2
    elif preferred_color_p1 == 'black' and preferred_color_p2 == 'white':
        print(f"Assigning white to {player2.get_display_name()} (both players prefer different colors)")
        return player2, player1
    
    # Priority 3: Balance overall color counts
    p1_white, p1_black = get_color_counts(tournament, player1)
    p2_white, p2_black = get_color_counts(tournament, player2)
    
    if p1_white - p1_black > p2_white - p2_black:
        print(f"Assigning white to {player2.get_display_name()} (color balance)")
        return player2, player1
    else:
        print(f"Assigning white to {player1.get_display_name()} (color balance)")
        return player1, player2

def assign_colors(player1, player2, tournament):
    """Determine who gets white based on previous color balance"""
    p1_white, p1_black = get_color_counts(tournament, player1)
    p2_white, p2_black = get_color_counts(tournament, player2)
    
    # If one player has had more whites, give white to the other
    if p1_white - p1_black > p2_white - p2_black:
        print(f"Assigning white to {player2.get_display_name()} because of color balance")
        return player2, player1  # player2 gets white
    print(f"Assigning white to {player1.get_display_name()} because of color balance")
    return player1, player2  # player1 gets white

import random

def generate_next_round(tournament):
    print("\n=== Generating Next Round (Round Robin) ===")

    participants = list(tournament.participants.filter(active=True).order_by('id'))
    num_players = len(participants)

    if num_players < 2:
        print("Not enough players to create pairings")
        return False

    # Add a dummy player for bye if odd number
    has_bye = False
    if num_players % 2 == 1:
        participants.append(None)
        has_bye = True
        num_players += 1
        print("Odd number of players, adding BYE placeholder")

    rounds = num_players - 1
    current_round = tournament.current_round + 1

    # Check for end of tournament
    if current_round > rounds:
        print("Tournament has reached all rounds")
        tournament.status = 'finished'
        tournament.save()
        return False

    half = num_players // 2

    # Rotate players according to round number
    players = participants[:]
    for _ in range(current_round - 1):
        # Proper circle rotation (keep first fixed)
        players = [players[0]] + [players[-1]] + players[1:-1]

    print(f"Round {current_round} pairings:")
    board_number = 1
    for i in range(half):
        p1 = players[i]
        p2 = players[num_players - 1 - i]

        # Handle bye
        if p1 is None or p2 is None:
            bye_player = p1 if p1 else p2
            if bye_player:
                print(f"{bye_player.get_display_name()} gets a bye this round")
                tournament.matches.create(
                    white_player=bye_player,
                    black_player=None,
                    result='bye',
                    round_number=current_round,
                    board_number=board_number
                )
                bye_player.has_bye = True
                bye_player.save()
            board_number += 1
            continue

        # Assign colors ensuring no player plays same color more than twice consecutively
        white, black = assign_colors_round_robin(p1, p2, tournament)

        print(f"Board {board_number}: {white.get_display_name()} (White) vs {black.get_display_name()} (Black)")
        tournament.matches.create(
            white_player=white,
            black_player=black,
            round_number=current_round,
            board_number=board_number,
            result='pending'
        )
        board_number += 1

    tournament.current_round = current_round
    tournament.save()
    print(f"Round {current_round} generation complete!")
    return True



def generate_next_round_old(tournament):
    print("\n=== Starting Next Round Generation ===")
    # Get active participants
    participants = list(tournament.participants.filter(active=True))
    print(f"Active participants: {[p.get_display_name() for p in participants]}")

    # If not enough players, return False
    if len(participants) < 2:
        print("Not enough players to create pairings")
        return False

    # For first round (current_round == 0)
    if tournament.current_round == 0:
        print("Generating first round pairings")
        # Shuffle players randomly
        random.shuffle(participants)

        # Create matches pairing adjacent players
        board_number = 1
        paired_players = set()  # Track who has been paired

        for i in range(len(participants)):
            if i in paired_players:
                continue

            # Handle odd number of players - give bye to last player
            if i == len(participants) - 1 and i not in paired_players:
                tournament.matches.create(
                    white_player=participants[i],
                    black_player=None,
                    result='bye',
                    round_number=1,
                    board_number=board_number
                )
                participants[i].has_bye = True  # Mark player as having received a bye
                participants[i].save()
                break

            # Find next unpaired player
            for j in range(i + 1, len(participants)):
                if j not in paired_players:
                    # Alternate colors for first round
                    if board_number % 2 == 0:
                        white, black = participants[i], participants[j]
                    else:
                        white, black = participants[j], participants[i]

                    tournament.matches.create(
                        white_player=white,
                        black_player=black,
                        round_number=1,
                        board_number=board_number
                    )
                    board_number += 1
                    paired_players.add(i)
                    paired_players.add(j)
                    break

        tournament.current_round = 1
        tournament.save()
        return True

    # For subsequent rounds
    # First check if current round is complete
    current_matches = tournament.matches.filter(round_number=tournament.current_round)
    print(f"Current round: {tournament.current_round}")
    if current_matches.exists() and current_matches.filter(result='pending').exists():
        print("Cannot generate next round - current round has pending matches")
        return False

    next_round = tournament.current_round + 1
    print(f"Generating pairings for round {next_round}")
    board_number = 1

    # Sort players by score
    sorted_players = sorted(participants, key=lambda p: (-p.score, -p.tiebreak_1, -p.tiebreak_2))
    print("\nPlayers sorted by score:")
    for p in sorted_players:
        print(f"{p.get_display_name()}: Score={p.score}, TB1={p.tiebreak_1}, TB2={p.tiebreak_2}")

    already_paired = set()  # Track players that have been paired this round
    matches_to_create = []

    # Try to pair players
    for i in range(len(sorted_players)):
        if i in already_paired:
            continue

        current_player = sorted_players[i]
        print(f"\nTrying to pair {current_player.get_display_name()}")
        opponent = None

        # Try to find an opponent who hasn't been paired and hasn't played against current_player
        for j in range(i + 1, len(sorted_players)):
            if j in already_paired:
                continue

            potential_opponent = sorted_players[j]
            print(f"Considering opponent: {potential_opponent.get_display_name()}")
            if not has_played_against(tournament, current_player, potential_opponent):
                opponent = potential_opponent
                already_paired.add(j)
                print(f"Found valid opponent: {opponent.get_display_name()}")
                break
            else:
                print(f"Skipping {potential_opponent.get_display_name()} - already played against")

        if opponent:
            white, black = assign_colors(current_player, opponent, tournament)
            match_data = {
                'white_player': white,
                'black_player': black,
                'round_number': next_round,
                'board_number': board_number
            }
            print(f"\nCreating match: Board {board_number}")
            print(f"White: {white.get_display_name()}")
            print(f"Black: {black.get_display_name()}")
            matches_to_create.append(match_data)
            board_number += 1
            already_paired.add(i)
        else:
            print(f"No valid opponent found for {current_player.get_display_name()}")

    # Handle remaining unpaired player (if odd number)
    unpaired = [p for i, p in enumerate(sorted_players) if i not in already_paired]
    if unpaired:
        last_player = unpaired[0]
        print(f"\nHandling unpaired player: {last_player.get_display_name()}")
        # Check if player hasn't received a bye before
        has_bye = tournament.matches.filter(white_player=last_player, black_player__isnull=True).exists()
        print(f"Player has previous bye: {has_bye}")
        if not has_bye:
            match_data = {
                'white_player': last_player,
                'black_player': None,
                'result': 'bye',
                'round_number': next_round,
                'board_number': board_number
            }
            print("Giving bye to player")
            matches_to_create.append(match_data)
            last_player.has_bye = True  # Mark player as having received a bye
            last_player.save()
        else:
            print("Skipping bye assignment to avoid repetition")

    # Create all matches
    print("\nCreating matches:")
    for match_data in matches_to_create:
        white = match_data['white_player']
        black = match_data['black_player']
        board = match_data['board_number']
        print(f"Creating match - Board {board}: {white.get_display_name()} vs {black.get_display_name() if black else 'BYE'}")
        tournament.matches.create(**match_data)

    # Update tournament round
    tournament.current_round = next_round
    tournament.save()
    print(f"\nRound {next_round} generation complete!")
    return True