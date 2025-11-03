from typing import List, Tuple
import random

def generate_next_round(tournament):
    # Get active participants
    participants = list(tournament.participants.filter(active=True))
    
    # If not enough players, return False
    if len(participants) < 2:
        return False
    
    # For first round (current_round == 0)
    if tournament.current_round == 0:
        # Shuffle players randomly
        random.shuffle(participants)
        
        # Create matches pairing adjacent players
        board_number = 1
        for i in range(0, len(participants), 2):
            # Handle odd number of players - last player gets a bye
            if i + 1 >= len(participants):
                # In future we might want to handle byes
                break
                
            tournament.matches.create(
                white_player=participants[i],
                black_player=participants[i + 1],
                round_number=1,
                board_number=board_number
            )
            board_number += 1
        
        # Update tournament round
        tournament.current_round = 1
        tournament.save()
        return True
    
    # For subsequent rounds
    # First check if current round is complete
    current_matches = tournament.matches.filter(round_number=tournament.current_round)
    if not current_matches.exists():
        # No matches in current round, proceed to next round
        next_round = tournament.current_round + 1
    else:
        # Check for pending matches
        pending_matches = current_matches.filter(result__exact='pending')
        if pending_matches.exists():
            return False
        
        next_round = tournament.current_round + 1
    
    # Generate next round pairings
    board_number = 1
    
    # Sort players by score for basic pairing
    sorted_players = sorted(participants, key=lambda p: (-p.score, -p.tiebreak_1, -p.tiebreak_2))
    
    # Create matches
    for i in range(0, len(sorted_players), 2):
        if i + 1 >= len(sorted_players):
            break  # Handle odd number of players
            
        white = sorted_players[i]
        black = sorted_players[i + 1]
        
        # Create the match
        tournament.matches.create(
            white_player=white,
            black_player=black,
            round_number=next_round,
            board_number=board_number
        )
        board_number += 1
    
    # Update tournament round
    tournament.current_round = next_round
    tournament.save()
    return True