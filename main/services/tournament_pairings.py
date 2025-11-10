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

def generate_next_round(tournament):
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